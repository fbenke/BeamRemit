from rest_framework import status
from beam.utils.json_response import JSONResponse


def page_not_found(request):
    return JSONResponse({'detail': 'Page Not Found'}, status=status.HTTP_404_NOT_FOUND)


def custom_error(request):
    return JSONResponse({'detail': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def permission_denied(request):
    return JSONResponse({'detail': 'Permission Denied'}, status=status.HTTP_403_FORBIDDEN)


def bad_request(request):
    return JSONResponse({'detail': 'Bad Request'}, status=status.HTTP_400_BAD_REQUEST)
