# Generated by Django 3.0.4 on 2020-03-14 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('email', models.EmailField(help_text='Email id of the user', max_length=255, unique=True)),
                ('name', models.CharField(help_text='Name of the user', max_length=255)),
                ('is_active', models.BooleanField(default=True, help_text='Active user')),
                ('is_superuser', models.BooleanField(default=False, help_text='Super user')),
                ('is_staff', models.BooleanField(default=False, help_text='Staff user')),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('refresh_token', models.CharField(default='', help_text='Refresh Token', max_length=512)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]