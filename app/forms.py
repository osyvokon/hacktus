from flask.ext.wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired

class SettingsForm(Form):
    cf_login = StringField('cf_login', validators=[DataRequired()])
