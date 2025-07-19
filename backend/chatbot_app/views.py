import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .rag_pipeline import answer_user_query
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render
from .models import MongoUser, ChatMessage
# @csrf_exempt
# def chat_page(request):
#     return render(request, "chat.html")


@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if MongoUser.objects(username=username).first():
            return JsonResponse({'error': 'Username already exists'}, status=400)

        user = MongoUser(username=username)
        user.set_password(password)
        user.save()

        return JsonResponse({'message': 'User created successfully'}, status=201)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = MongoUser.objects(username=username).first()
        if user and user.check_password(password):
            request.session['user_id'] = str(user.id)
            request.session['username'] = user.username
            return JsonResponse({'message': 'Login successful'})
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


@csrf_exempt
def logout_view(request):
    request.session.flush()
    return JsonResponse({'message': 'Logged out successfully'})

@csrf_exempt
def user_view(request):
    username = request.session.get('username')
    if username:
        return JsonResponse({'username': username})
    return JsonResponse({'user': None}, status=401)


@csrf_exempt
def chatbot_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            query = data.get("query", "")
            response, sources = answer_user_query(query)

            # 🛠 Extract source filenames only
            simplified_sources = [doc.metadata.get("source", "Unknown") for doc in sources]

            return JsonResponse({
                "response": str(response.content) if hasattr(response, "content") else str(response),
                "sources": simplified_sources[:3]
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"message": "Only POST method is allowed"})


# @csrf_exempt
# def chatbot_view(request):
#     if request.method == "POST":
#         try:
#             # ✅ Check if user is logged in
#             user_id = request.session.get("user_id")
#             if not user_id:
#                 return JsonResponse({"error": "Unauthorized"}, status=401)

#             user = MongoUser.objects(id=user_id).first()
#             if not user:
#                 return JsonResponse({"error": "User not found"}, status=404)

#             # ✅ Process the query
#             data = json.loads(request.body)
#             query = data.get("query", "")
#             response, sources = answer_user_query(query)

#             # ✅ Extract source filenames only
#             simplified_sources = [doc.metadata.get("source", "Unknown") for doc in sources]

#             # ✅ Save to history
#             user.history.append(ChatMessage(
#                 query=query,
#                 response=str(response.content) if hasattr(response, "content") else str(response)
#             ))
#             user.save()

#             return JsonResponse({
#                 "response": str(response.content) if hasattr(response, "content") else str(response),
#                 "sources": simplified_sources[:3]
#             })

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)

#     return JsonResponse({"message": "Only POST method is allowed"})


@csrf_exempt
def get_history_view(request):
    if request.method == "GET":
        # ✅ Check if user is logged in
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        user = MongoUser.objects(id=user_id).first()
        if not user:
            return JsonResponse({"error": "User not found"}, status=404)

        # ✅ Serialize the user's chat history
        history_data = [
            {
                "query": msg.query,
                "response": msg.response,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in user.history
        ]

        return JsonResponse({"history": history_data}, status=200)

    return JsonResponse({"message": "Only GET method is allowed"}, status=405)