from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Review
from .serializers import ReviewSerializer, ReviewAdminUpdateSerializer
from django.utils.timezone import now

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

# Admin tomonidan sharhni tasdiqlash yoki rad etish
class ReviewAdminUpdateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            review = Review.objects.get(pk=pk)
            serializer = ReviewAdminUpdateSerializer(review, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(updated_admin=request.user, updated_at=now())
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
        except Review.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)
