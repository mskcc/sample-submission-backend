from flask import Flask, render_template, Blueprint

upload = Blueprint('upload', __name__)


@upload.route("/")
def welcome():
    return "Sample Receiving Backend"


