# from rest_framework.views import exception_handler
# from rest_framework.response import Response
#
#
# def custom_exception_handler(exc, context):
#     # Call REST framework's default exception handler first,
#     # to get the standard error response.
#     response = exception_handler(exc, context)
#     # Now add the HTTP status code to the response.
#     if response is None:
#         view = context['view']  # 出错的视图
#         error = 'server error, %s' % exc
#         print('%s: %s' % (view, error))
#         return Response({
#             'detail': error
#         }, status=500)
#
#     return response
