from flask.ext.wtf import Form
from wtforms import StringField
from wtforms.fields import PasswordField
from wtforms.validators import DataRequired


class SettingsForm(Form):
    cf_login = StringField('cf_login', validators=[DataRequired()])


# class TopcoderAuthForm(Form):
# 	tp_name = StringField('username', validators[DataRequired()])
# 	tp_pwd = PasswordField('password', validators[DataRequired()])
