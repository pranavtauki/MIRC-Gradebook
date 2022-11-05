# Generated by Django 4.1.2 on 2022-11-03 18:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gradebook_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gradebook_app.course')),
                ('profile_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gradebook_app.profile')),
            ],
        ),
    ]
