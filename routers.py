import json
import os
import sys
import time
from datetime import datetime
from multiprocessing import Process
from random import randint, choice

import firebase_admin
import fitz
import pytz
from firebase_admin import credentials
from firebase_admin import firestore
from flask import redirect
from flask import render_template, url_for, send_file
from flask import request
from werkzeug.utils import secure_filename

from server import app

cred = credentials.Certificate(os.path.join(sys.path[0], "creds.json"))
firebase_admin.initialize_app(cred)

db = firestore.client()


@app.route('/')
def home_page():
    return render_template('home.html')


@app.route('/registration')
def go_registration():
    return render_template('register.html')


@app.route('/login')
def go_login():
    return render_template('login.html')


@app.route('/categories')
def go_categories():
    colors = ['primary', 'success', 'danger', 'info', 'warning']
    return render_template('categories.html', categories={'Classic': {'sub': ['Avant-Garde',
                                                                              'Baroque',
                                                                              'Chant'],
                                                                      'visitors': randint(100, 1000),
                                                                      'colors': [choice(colors) for _ in colors]
                                                                      },
                                                          'Fiction': {'sub': ['Avant-Garde',
                                                                              'Baroque',
                                                                              'Chant'],
                                                                      'visitors': randint(100, 1000),
                                                                      'colors': [choice(colors) for _ in colors]
                                                                      },
                                                          'Thriller': {'sub': ['Avant-Garde',
                                                                               'Baroque',
                                                                               'Chant'],
                                                                       'visitors': randint(100, 1000),
                                                                       'colors': [choice(colors) for _ in colors]
                                                                       },
                                                          'History': {'sub': ['Avant-Garde',
                                                                              'Baroque',
                                                                              'Chant'],
                                                                      'visitors': randint(100, 1000),
                                                                      'colors': [choice(colors) for _ in colors]
                                                                      },
                                                          'Others': {'sub': ['Avant-Garde',
                                                                             'Baroque',
                                                                             'Chant'],
                                                                     'visitors': randint(100, 1000),
                                                                     'colors': [choice(colors) for _ in colors]
                                                                     }})


@app.route('/share_books')
def go_share_books():
    return render_template('share_books.html')


def parse_first_image(file_path: str):
    pdf_document_object = fitz.open(file_path)
    page = pdf_document_object.loadPage(0)
    pix = page.getPixmap(matrix=fitz.Matrix(2, 2))  # 300 DPI
    pix.writePNG(
        os.path.join(sys.path[0], 'static', 'pdf_images', "{}.png".format(
            file_path.split("/")[-1])))
    print("Done fetching..")
    return


@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    f = request.files
    print(f['pdf'])
    filename = secure_filename(f['pdf'].filename).lstrip().rstrip()
    if filename:
        full_file_path = os.path.join(sys.path[0], 'static', 'pdf', "{}".format(filename))
        f['pdf'].save(full_file_path)
        Process(target=parse_first_image, args=(full_file_path,)).start()
    return redirect(url_for('go_share_books'))


@app.route('/profile')
def go_profile():
    return render_template('profile.html')


@app.route('/shops')
def go_shops():
    return render_template('shop.html', shops=['BookStore', 'Websites', 'Buy PDF'])


@app.route('/about_us')
def go_about_us():
    return render_template('about_us.html')


@app.route('/reviews')
def go_reviews():
    users_ref = db.collection(u'user-review')
    docs = users_ref.stream()
    # for doc in docs:
    #     print(f'{doc.id} => {doc.to_dict()}')
    r = [doc.to_dict() for doc in docs] * 10
    reviews = [r[i:i + 3] for i in range(0, len(r), 3)]
    print(reviews)
    return render_template('reviews.html', reviews=reviews)


@app.route('/authors')
def go_authors():
    return render_template('authors.html')


@app.route('/read_in')
def go_read_in():
    books = [{'book_name': b,
              'read_by': randint(100, 1000),
              'book_size': round((os.path.getsize(os.path.join(sys.path[0], 'static', 'pdf', b))) / (1024 ** 2), 2)}
             for b in os.listdir(os.path.join(sys.path[0], 'static', 'pdf')) if b.endswith(".pdf")]
    books = [books[i:i + 2] for i in range(0, len(books), 2)]
    print(books)
    return render_template('read_in.html', books=books)


@app.route('/read_pdf/<pdf_name>')
def read_pdf(pdf_name: str):
    assert pdf_name in os.listdir(os.path.join(sys.path[0], 'static', 'pdf'))
    return render_template('read_pdf.html', pdf_name=pdf_name)


@app.route('/download_pdf/<pdf_name>')
def download_pdf(pdf_name: str):
    print(pdf_name)
    assert pdf_name in os.listdir(os.path.join(sys.path[0], 'static', 'pdf'))
    return send_file(os.path.join(sys.path[0], 'static', 'pdf', pdf_name), as_attachment=True)


@app.route('/search_for_book/<query_string>')
def search_for_book(query_string):
    books = [{'book_name': b,
              'read_by': randint(100, 1000),
              'book_size': round((os.path.getsize(os.path.join(sys.path[0], 'static', 'pdf', b))) / (1024 ** 2), 2)}
             for b in os.listdir(os.path.join(sys.path[0], 'static', 'pdf')) if b.endswith(".pdf") and
             b.lower().find(query_string.lower()) != -1]
    books = [books[i:i + 2] for i in range(0, len(books), 2)]
    return render_template('search_result.html', books=books)


@app.route('/submit_review', methods=['POST'])
def submit_review():
    f = request.form
    doc_ref = db.collection(u'user-review').document(u'{}'.format(int(time.time())))
    doc_ref.set({
        u'username': f['user_name'],
        u'review_text': f['review_text'],
        u'when': datetime.now(pytz.timezone('Asia/Dhaka')).strftime("%I:%M:%S %p %d %B,%Y")
    })
    return redirect(url_for('go_reviews'))
