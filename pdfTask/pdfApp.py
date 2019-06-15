from flask import Flask, request, render_template
import os
import simplejson
import string
from flask_sqlalchemy import SQLAlchemy
import PyPDF2
from collections import Counter
import re
from datetime import datetime, timedelta

# flask run in directory
# submit and get data displayed on html

# pdf only
ALLOWED_EXTENSIONS = set(['pdf'])
# Sqlite3 db connection using SQLAlchemy
file_path = os.path.abspath(os.getcwd()) + "/top5.db"
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + file_path
app.app_context().push()
db = SQLAlchemy(app)


# db file model
class FileContents(db.Model):
    Id = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(64), index=True)
    Top5 = db.Column(db.String(120), index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())


# check files to make sure it is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# main route used to get or set data
@app.route('/')
def index():
    return render_template('home.html')


# upload file route + POST
@app.route('/Upload_file', methods=['POST'])
def upload_file():
    # my sample.pdf is broken and only returns
    file_test = request.files['inputFile']
    text_blob = ''
    # creating a pdf reader object
    pdf_reader = PyPDF2.PdfFileReader(file_test)

    number_of_pages = pdf_reader.getNumPages()
    for page_number in range(number_of_pages):
        # creating a page object
        page_obj = pdf_reader.getPage(page_number)
        text_blob += page_obj.extractText()
    # extracting text from page and removing special characters
    text_blob = text_blob + ''.join([x for x in text_blob if x in string.ascii_letters + '\'- '])
    text_blob = re.sub('[!@#$-]', '', text_blob)
    words = text_blob.split()
    # Pass the words list to instance of Counter class.
    word_count = Counter(words)

    # most_occur() produces k frequently encountered
    # input values and their respective counts.
    most_occur = word_count.most_common(5)
    top5 = ','.join(map(str, most_occur))

    # add parsed content to a variable ready to be sent to the db
    new_file = FileContents(Title=file_test.filename, Top5=top5, timestamp=datetime.utcnow())
    db.session.add(new_file)
    db.session.commit()
    # render submit template to confirm submit and allow for navigation
    return render_template('submit.html', result=file_test.filename)


# used to convert datetime quickly to add to json object
def my_converter(o):
    if isinstance(o, datetime):
        return o.__str__()


# GET route used to get submitted file information
@app.route('/get-common-words', methods=['GET'])
def get_file():
    # I ran into issues with files_dict overwriting itself
    # so I used a second list to grab all data
    file_data = FileContents.query.all()
    files_dict = []
    files_dict2 = []
    # for loop over each item in the dictionary
    for item in file_data:
        timestamp = simplejson.dumps(item.timestamp, default=my_converter)
        item.timestamp = timestamp
        files_dict = {
            'Key': item.Id,
            'Title': item.Title,
            'Top5': item.Top5,
            'timestamp': item.timestamp}
        files_dict.update(files_dict)
        files_dict2.append(files_dict)
    # for loop to print all entries
    for i in files_dict2:
        print(i)
    # render all entries
    return render_template('get.html', result=files_dict2)


if __name__ == "__main__":
    app.run()
