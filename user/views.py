from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserCreateSerializer


class UserRegistrationView(generics.CreateAPIView):
    """ Api to register the user """
    serializer_class = UserCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "User registration successful"},
            status=status.HTTP_201_CREATED
        )


class LogoutAndBlacklistTokenView(APIView):
    """ Api to log out the user """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if "refresh_token" not in request.data:
            return Response({"message": "Please provide refresh_token in the body"})
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "User logged out successfully."})
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
