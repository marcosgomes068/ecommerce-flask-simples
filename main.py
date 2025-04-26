from flask import *
from flask_sqlalchemy import *
from flask_login import *
from flask_bootstrap import *
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seuemail@gmail.com'  
app.config['MAIL_PASSWORD'] = 'suasenha'            

from models import *
from forms import RequestResetForm, ResetPasswordForm
from forms import *
db.init_app(app)

Bootstrap(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

mail = Mail(app)

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET'])
def index():
    q = request.args.get('q', '').strip()
    categoria = request.args.get('categoria', '').strip()
    preco_min = request.args.get('preco_min', '').strip()
    preco_max = request.args.get('preco_max', '').strip()
    products = Product.query
    if q:
        products = products.filter(Product.name.ilike(f'%{q}%'))
    if categoria:
        products = products.filter(Product.category.ilike(f'%{categoria}%'))
    if preco_min:
        try:
            products = products.filter(Product.price >= float(preco_min))
        except ValueError:
            pass
    if preco_max:
        try:
            products = products.filter(Product.price <= float(preco_max))
        except ValueError:
            pass
    products = products.all()
    categorias = db.session.query(Product.category).distinct().all()
    categorias = [c[0] for c in categorias if c[0]]
    return render_template('index.html', products=products, q=q, categoria=categoria, preco_min=preco_min, preco_max=preco_max, categorias=categorias)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email já cadastrado.', 'error')
            return redirect(url_for('register'))
        user = User(username=form.username.data, email=form.email.data)
        user.password = generate_password_hash(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Usuário criado! Faça login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos!', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado!', 'success')
    return redirect(url_for('index'))

@app.route('/produto/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    if not current_user.is_admin:
        flash('Apenas administradores podem cadastrar produtos!', 'error')
        return redirect(url_for('index'))
    form = ProductForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            image = form.image.data
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        produto = Product(
            name=form.name.data,
            price=form.price.data,
            description=form.description.data,
            category=form.category.data,
            image=filename
        )
        db.session.add(produto)
        db.session.commit()
        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('index'))
    return render_template('product_form.html', form=form)

@app.route('/produto/editar/<int:product_id>', methods=['GET', 'POST'])
@login_required
def editar_produto(product_id):
    if not current_user.is_admin:
        flash('Acesso negado!', 'error')
        return redirect(url_for('index'))
    produto = Product.query.get_or_404(product_id)
    form = ProductForm(obj=produto)
    if form.validate_on_submit():
        produto.name = form.name.data
        produto.price = form.price.data
        produto.description = form.description.data
        produto.category = form.category.data
        if form.image.data:
            image = form.image.data
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            produto.image = filename
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin'))
    return render_template('product_form.html', form=form, editar=True)

@app.route('/produto/excluir/<int:product_id>', methods=['POST'])
@login_required
def excluir_produto(product_id):
    if not current_user.is_admin:
        flash('Acesso negado!', 'error')
        return redirect(url_for('index'))
    produto = Product.query.get_or_404(product_id)
    db.session.delete(produto)
    db.session.commit()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('admin'))

@app.route('/add_carrinho/<int:product_id>')
def add_carrinho(product_id):
    product = Product.query.get_or_404(product_id)
    carrinho = session.get('carrinho', {})
    if str(product_id) in carrinho:
        carrinho[str(product_id)] += 1
    else:
        carrinho[str(product_id)] = 1
    session['carrinho'] = carrinho
    flash(f'{product.name} adicionado ao carrinho!', 'success')
    return redirect(url_for('index'))

@app.route('/carrinho')
def carrinho():
    carrinho = session.get('carrinho', {})
    produtos = []
    total = 0
    for pid, qtd in carrinho.items():
        prod = Product.query.get(int(pid))
        if prod:
            subtotal = prod.price * qtd
            produtos.append({'produto': prod, 'quantidade': qtd, 'subtotal': subtotal})
            total += subtotal
    return render_template('carrinho.html', produtos=produtos, total=total)

@app.route('/remover_carrinho/<int:product_id>')
def remover_carrinho(product_id):
    carrinho = session.get('carrinho', {})
    pid = str(product_id)
    if pid in carrinho:
        carrinho.pop(pid)
        session['carrinho'] = carrinho
        flash('Produto removido do carrinho!', 'success')
    return redirect(url_for('carrinho'))

@app.route('/pedido/<int:pedido_id>')
@login_required
def detalhes_pedido(pedido_id):
    pedido = Order.query.get_or_404(pedido_id)
    if pedido.user_id != current_user.id and not current_user.is_admin:
        flash('Acesso negado!', 'error')
        return redirect(url_for('meus_pedidos'))
    return render_template('detalhes_pedido.html', pedido=pedido)

@app.route('/reset_senha', methods=['GET', 'POST'])
def reset_senha():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = serializer.dumps(user.email, salt='reset-senha')
            link = url_for('reset_token', token=token, _external=True)
            msg = Message('Recuperação de senha', sender=app.config['MAIL_USERNAME'], recipients=[user.email])
            msg.body = f'Para redefinir sua senha, clique no link: {link}\nSe não solicitou, ignore este email.'
            mail.send(msg)
        flash('Se o e-mail existir, enviamos as instruções de recuperação.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_senha.html', form=form)

@app.route('/reset_senha/<token>', methods=['GET', 'POST'])
def reset_token(token):
    try:
        email = serializer.loads(token, salt='reset-senha', max_age=3600)
    except Exception:
        flash('O link de redefinição expirou ou é inválido.', 'error')
        return redirect(url_for('reset_senha'))
    user = User.query.filter_by(email=email).first_or_404()
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = form.password.data
        db.session.commit()
        flash('Senha redefinida com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', form=form)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
