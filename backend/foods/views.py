from django.db.models import Sum, F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework import (filters, status, mixins)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (AllowAny, IsAuthenticated)
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .filters import RecipeFilter, IngredientFilter
from .serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeListSerializer,
    RecipeCreateUpdateSerializer,
    TagSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    UserSubscriptionsSerializer,
    UserGetSerializer,
    UserPostSerializer
)
from recipes.models import (
    Favorite,
    Ingredient,
    RecipeIngredient,
    Recipe,
    Tag,
    ShoppingCart
)
from users.models import Subscription, User
from .permissions import AuthorPermission
from .pagination import DefaultPaginator


class DefaultUserViewSet(UserViewSet):
    queryset = User.objects.all()
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAuthenticated,)
    pagination_class = DefaultPaginator
    search_fields = ('username', 'email')
    lookup_fields = ('name', 'id')
    http_method_names = ['get', 'post', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserGetSerializer
        return UserPostSerializer

    @action(detail=False, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            context={
                'request': request
            },
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['id'])
        user = request.user
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                context={
                    "request": request
                },
                data={
                    'user': user.id,
                    'author': author.id
                }
            )
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription_exists = Subscription.objects.filter(
            user=user, author=author).exists()
        if not subscription_exists:
            return Response(
                {
                    'errors': 'Вы не подписаны на этого автора'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[AuthorPermission])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = UserSubscriptionsSerializer(
            page,
            many=True,
            context={
                'request': request
            }
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = DefaultPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        user = request.user
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={
                    'user': user.id,
                    'recipe': recipe.id
                }
            )
            serializer.is_valid(raise_exception=True)
            Favorite.objects.create(user=user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        favorite = Favorite.objects.filter(user=user.id, recipe=recipe.id)
        if not favorite:
            return Response(
                {
                    'errors': 'Рецепта нет в избранном'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[AuthorPermission])
    def download_shopping_cart(self, request):
        items = RecipeIngredient.objects.select_related(
            'recipe', 'ingredient'
        )
        items = items.filter(recipe__shopping_carts__user=request.user).all()
        shopping_cart = items.values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            name=F('ingredient__name'),
            units=F('ingredient__measurement_unit'),
            total=Sum('amount')
        ).order_by('-total')
        text = '\n'.join(
            [f"{item.get('name')} ({item.get('units')}) - {item.get('total')}"
             for item in shopping_cart]
        )
        filename = 'foodgram_shopping_cart.txt'
        response = HttpResponse(text, content_type='text/plan')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        user = request.user
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                context={
                    "request": request
                },
                data={
                    'user': user.id,
                    'recipe': recipe.id
                }
            )
            serializer.is_valid(raise_exception=True)
            ShoppingCart.objects.create(user=user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_200_OK)

        shopping_cart = ShoppingCart.objects.filter(
            recipe=recipe.id, user=user.id)
        if not shopping_cart:
            return Response(
                {
                    'errors': 'Этого рецепта нет в списке покупок'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
