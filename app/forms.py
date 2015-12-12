from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField
from wtforms.validators import DataRequired

class LoginForm(Form):
    gh_login = StringField('gh_login', validators=[DataRequired()])
    gh_password = PasswordField('gh_password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)
