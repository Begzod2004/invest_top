from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Review
from .serializers import ReviewSerializer, ReviewAdminUpdateSerializer
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema, extend_schema_view

# Foydalanuvchi sharh qoldirishi uchun
class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Barcha sharhlarni ko'rish (Adminlar uchun)
class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Review.objects.all().order_by('-created_at')

# Sharhni o'zgartirish yoki o'chirish
class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Review.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(user=user)

@extend_schema(
    tags=['reviews'],
    request=ReviewAdminUpdateSerializer,
    responses={200: ReviewSerializer}
)
class ReviewAdminUpdateView(APIView):
    """
    Admin tomonidan sharhni tasdiqlash yoki rad etish
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ReviewAdminUpdateSerializer

    def post(self, request, pk):
        try:
            review = Review.objects.get(pk=pk)
            serializer = self.serializer_class(review, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(updated_admin=request.user, updated_at=now())
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
        except Review.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)

@extend_schema_view(
    list=extend_schema(
        tags=['reviews'],
        summary="Sharhlar ro'yxati",
        description="Barcha sharhlarni ko'rish"
    ),
    create=extend_schema(
        tags=['reviews'],
        summary="Sharh qoldirish",
        description="Yangi sharh qo'shish"
    ),
    retrieve=extend_schema(
        tags=['reviews'],
        summary="Sharh ma'lumotlari",
        description="Sharh haqida to'liq ma'lumot"
    ),
    update=extend_schema(
        tags=['reviews-admin'],
        summary="Sharhni tahrirlash",
        description="Sharhni tahrirlash (Admin)"
    ),
    destroy=extend_schema(
        tags=['reviews-admin'],
        summary="Sharhni o'chirish",
        description="Sharhni o'chirish (Admin)"
    )
)
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

class ReviewListViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
