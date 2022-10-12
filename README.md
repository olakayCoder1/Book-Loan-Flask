# Book-Loan-Flask
This project is a book reading loan website ( API ). Built with Flask .
## Project functionality
  - Registration
  - Login
  - Two factor authentication
  - Password reset
  - Book list
  - Loan history
  
 Admin 
  - coming soon
  

## Testing the project 

clone the repository
```sh
git clone https://github.com/olakayCoder1/Book-Loan-Flask
```
Cd to folder
```sh
cd Book-Loan-Flask
```
Create a virtual environment 
```sh
python -m venv <virtaulenv name>
```
Activate virtual environment 
```sh
venv\scripts\activate
```
Install requirement library

```sh
pip install requirements.txt
```
Cd to project 
```sh
cd project
```
Create the database in the terminal
```sh
flask shell
```
Create db
```sh
from mail_tracker import db
db.create_all()
exit()
```
Run the flask server
```sh
flask run
```
If you like it do not forget to give it a star
