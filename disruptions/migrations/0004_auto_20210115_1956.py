# Generated by Django 3.1.5 on 2021-01-15 19:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('disruptions', '0003_delete_stopsuspension'),
    ]

    operations = [
        migrations.AlterField(
            model_name='situation',
            name='source',
            field=models.ForeignKey(limit_choices_to={'name__in': ['Transport for the North', 'bustimes.org']}, on_delete=django.db.models.deletion.CASCADE, to='busstops.datasource'),
        ),
    ]
