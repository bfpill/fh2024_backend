import requests

# Replace 'your_fastapi_server_url' with the actual URL of your FastAPI server
fastapi_url = 'http://localhost:8000'

# # ### Create user 
# og_email = 'davidb@gmail.com'
# def encode_email(email):
#     return email.replace('.', ',')

# response_create_user = requests.post(fastapi_url + f'/api/create_user/{encode_email(email)}', json={"email": email})
# print(response_create_user.json())



# # ## Push sample book data to firebase
# book_id = '104'
# book_data = {
#     "title": "Sample Book random Title 1",
#     "category": "Science",
#     "pages": [
#         {
#             "pageNum": 1,
#             "text": "Page 1 Content: Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
#             "images": [
#                 "The Steam Age Exhibit",
#                 "Coal-Powered Steam Train"
#             ]
#         },
#         {
#             "pageNum": 2,
#             "text": "Page 2 Content: Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
#             "images": [
#                 "The Steam Age Exhibit",
#                 "Coal-Powered Steam Train"
#             ]
#         }
#     ]
# }

# response_push_book = requests.post(fastapi_url + f"/api/set_book/{encode_email(og_email)}/{book_id}", json=book_data)
# print(response_push_book.json())



# ### Get book by user id and book id 
# book_id = 104
# print(fastapi_url + f'/api/get_book/{encode_email(og_email)}/{book_id}')
# response_get_book = requests.get(fastapi_url + f'/api/get_book/{encode_email(og_email)}/{book_id}')
# print(response_get_book.json())


# # ### Get all books
# response_get_all_books = requests.get(fastapi_url + '/api/get_all_books')
# print(response_get_all_books.json())


# ## get all books for user
# response_get_user_books = requests.get(fastapi_url + f'/api/user_books/max@v3rv,com')
# print(response_get_user_books.json())