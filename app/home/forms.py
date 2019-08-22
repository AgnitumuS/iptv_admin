from flask_wtf import FlaskForm
from flask_babel import lazy_gettext

from wtforms.fields import StringField, SubmitField, TextAreaField
from wtforms.validators import InputRequired, Length, Email


class ContactForm(FlaskForm):
    email = StringField(lazy_gettext(u'Email:'),
                        validators=[InputRequired(), Email(message=lazy_gettext(u'Please enter your email address.')),
                                    Length(max=30)])
    subject = StringField(lazy_gettext(u'Subject:'),
                          validators=[InputRequired('Please enter a subject.'), Length(min=1, max=80)])
    message = TextAreaField(lazy_gettext(u'Message:'), validators=[InputRequired(message=lazy_gettext(
        u'Please enter a message.')), Length(min=1, max=500)])
    submit = SubmitField(lazy_gettext(u'Send'))
