# Generated by Django 5.0.6 on 2024-07-30 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stream_video', '0002_rename_user_video_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='category',
            field=models.CharField(choices=[('Education', 'Education'), ('Entertainment', 'Entertainment'), ('Music', 'Music'), ('News', 'News'), ('Sports', 'Sports'), ('Technology', 'Technology'), ('Gaming', 'Gaming'), ('Other', 'Other')], default='Other', max_length=20),
        ),
    ]
