# Generated by Django 4.1.5 on 2023-02-08 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # ("vehicles", "0019_remove_vehiclejourney_block"),
        ("bustimes", "0010_trip__block_trip_vehicle_journey_code_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="trip",
            name="_block",
        ),
        migrations.AlterField(
            model_name="trip",
            name="block",
            field=models.CharField(
                blank=True, db_index=True, default="", max_length=100
            ),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name="Block",
        ),
    ]
