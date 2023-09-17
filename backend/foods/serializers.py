from django.db import transaction
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    RecipeIngredient,
    Tag,
    Recipe,
    ShoppingCart)
from users.models import Subscription, User


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Ingredient


class UserGetSerializer(UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        authenticated = self.context['request'].user.is_authenticated
        subscribed = Subscription.objects.filter(
            author=obj, user=self.context['request'].user
        ).exists()
        return authenticated and subscribed

    class Meta:
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        model = User


class UserPostSerializer(UserCreateSerializer):
    class Meta:
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        model = User


class UserSubscriptionsSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        authenticated = self.context['request'].user.is_authenticated
        subscribed = Subscription.objects.filter(
            author=obj, user=self.context['request'].user
        ).exists()
        return authenticated and subscribed

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                raise serializers.ValidationError(
                    'Параметр limit должен быть целочисленным'
                )
            recipes = recipes[:limit]
        serializer = RecipeMinifiedSerializer(
            recipes, many=True, read_only=True
        )
        return serializer.data

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    def validate_author(self, author):
        if self.context['request'].user == author:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        return author

    def to_representation(self, instance):
        author = instance['author']
        return UserSubscriptionsSerializer(author, context=self.context).data

    class Meta:
        fields = '__all__'
        model = Subscription
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны'
            ),
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    @transaction.atomic
    def create(self, validated_data):
        return RecipeIngredient.objects.create(
            ingredient=validated_data.pop('ingredient'),
            amount=validated_data.pop('amount'),
            recipe=validated_data.pop('recipe')
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        recipe_ingredient = get_object_or_404(
            RecipeIngredient,
            ingredient=validated_data.get('ingredient'),
            amount=validated_data.get('amount'),
            recipe=validated_data.get('recipe')
        )
        if validated_data:
            recipe_ingredient.save()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    image = Base64ImageField()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        read_only=True,
        source='recipes'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )

    @staticmethod
    def validate_ingredients(data):
        if not data:
            raise serializers.ValidationError('Добавьте ингредиент')

        ids = []
        for _, val in enumerate(data):
            ids.append(val['id'])
        ingredients = list(Ingredient.objects.filter(
            id__in=ids).values_list('id', flat=True))

        if len(ingredients) != len(data):
            raise serializers.ValidationError('Ингредиента не существует')
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError('Ингредиенты повторяются')
        return data

    @staticmethod
    def validate_amount(amount):
        if not amount:
            raise serializers.ValidationError('Продукт не указан')
        return amount

    @staticmethod
    def validate_cooking_time(cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError('Время должно быть больше 1 мин')
        return cooking_time

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            **validated_data,
            author=self.context['request'].user
        )
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        if tags is not None:
            recipe.tags.set(tags)
        if ingredients is not None:
            recipe.ingredients.clear()
            RecipeIngredient.objects.bulk_create(
                [RecipeIngredient(
                    recipe=recipe,
                    ingredient_id=ingredient['id'],
                    amount=ingredient['amount']
                ) for ingredient in ingredients]
            )

        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        recipe = instance['recipe']
        return RecipeMinifiedSerializer(recipe, context=self.context).data

    class Meta:
        fields = ('user', 'recipe')
        model = Favorite
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном'
            ),
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    def validate_recipe(self, data):
        user = self.context['request'].user
        if ShoppingCart.objects.filter(recipe=data, user=user).exists():
            raise serializers.ValidationError('Рецепт уже есть в корзине')
        return data

    def to_representation(self, instance):
        recipe = instance['recipe']
        return RecipeMinifiedSerializer(recipe).data

    class Meta:
        fields = ('user', 'recipe')
        model = ShoppingCart
