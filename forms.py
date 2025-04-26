from flask_wtf import *
from wtforms import *
from wtforms.validators import *

class RegisterForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirme a senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar link de redefinição')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirme a nova senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Redefinir Senha')

class ProductForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired()])
    price = FloatField('Preço', validators=[DataRequired()])
    description = TextAreaField('Descrição', validators=[DataRequired()])
    image = FileField('Imagem')
    category = StringField('Categoria')
    submit = SubmitField('Salvar')
