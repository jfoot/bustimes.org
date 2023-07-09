# Generated by Django 4.2.3 on 2023-07-09 13:39

import bustimes.fields
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.text


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('vosa', '0001_initial'),
        ('busstops', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankHoliday',
            fields=[
                ('id', models.SmallAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Calendar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mon', models.BooleanField()),
                ('tue', models.BooleanField()),
                ('wed', models.BooleanField()),
                ('thu', models.BooleanField()),
                ('fri', models.BooleanField()),
                ('sat', models.BooleanField()),
                ('sun', models.BooleanField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('summary', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Garage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=50)),
                ('name', models.CharField(blank=True, max_length=100)),
                ('location', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('operator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='busstops.operator')),
            ],
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=16)),
                ('text', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=255)),
                ('service_code', models.CharField(blank=True, max_length=255)),
                ('line_brand', models.CharField(blank=True, max_length=255)),
                ('line_name', models.CharField(blank=True, max_length=255)),
                ('revision_number', models.PositiveIntegerField(default=0)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('outbound_description', models.CharField(blank=True, max_length=255)),
                ('inbound_description', models.CharField(blank=True, max_length=255)),
                ('origin', models.CharField(blank=True, max_length=255)),
                ('destination', models.CharField(blank=True, max_length=255)),
                ('via', models.CharField(blank=True, max_length=255)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('public_use', models.BooleanField(null=True)),
                ('registration', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='vosa.registration')),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='busstops.service')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busstops.datasource')),
            ],
        ),
        migrations.CreateModel(
            name='VehicleType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=50)),
                ('description', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inbound', models.BooleanField(default=False)),
                ('journey_pattern', models.CharField(blank=True, max_length=100)),
                ('vehicle_journey_code', models.CharField(blank=True, db_index=True, max_length=100)),
                ('ticket_machine_code', models.CharField(blank=True, db_index=True, max_length=100)),
                ('block', models.CharField(blank=True, db_index=True, max_length=100)),
                ('sequence', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('start', bustimes.fields.SecondsField()),
                ('end', bustimes.fields.SecondsField()),
                ('calendar', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='bustimes.calendar')),
                ('destination', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='busstops.stoppoint')),
                ('garage', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bustimes.garage')),
                ('next_trip', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bustimes.trip')),
                ('notes', models.ManyToManyField(blank=True, to='bustimes.note')),
                ('operator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='busstops.operator')),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bustimes.route')),
                ('vehicle_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bustimes.vehicletype')),
            ],
            options={
                'index_together': {('route', 'start', 'end')},
            },
        ),
        migrations.CreateModel(
            name='TimetableDataSource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('search', models.CharField(blank=True, max_length=255)),
                ('url', models.URLField(blank=True)),
                ('modified_at', models.DateTimeField(blank=True, null=True)),
                ('settings', models.JSONField(blank=True, null=True)),
                ('complete', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=True)),
                ('operators', models.ManyToManyField(blank=True, to='busstops.operator')),
                ('region', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='busstops.region')),
            ],
        ),
        migrations.CreateModel(
            name='CalendarDate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(db_index=True)),
                ('end_date', models.DateField(blank=True, db_index=True, null=True)),
                ('operation', models.BooleanField(db_index=True)),
                ('special', models.BooleanField(db_index=True, default=False)),
                ('summary', models.CharField(blank=True, max_length=255)),
                ('calendar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bustimes.calendar')),
            ],
        ),
        migrations.CreateModel(
            name='CalendarBankHoliday',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operation', models.BooleanField()),
                ('bank_holiday', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bustimes.bankholiday')),
                ('calendar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bustimes.calendar')),
            ],
        ),
        migrations.AddField(
            model_name='calendar',
            name='bank_holidays',
            field=models.ManyToManyField(through='bustimes.CalendarBankHoliday', to='bustimes.bankholiday'),
        ),
        migrations.CreateModel(
            name='BankHolidayDate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('scotland', models.BooleanField(help_text='Yes = Scotland only, No = not Scotland, Unknown = both', null=True)),
                ('bank_holiday', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bustimes.bankholiday')),
            ],
        ),
        migrations.CreateModel(
            name='StopTime',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('stop_code', models.CharField(blank=True, max_length=255)),
                ('arrival', bustimes.fields.SecondsField(blank=True, null=True)),
                ('departure', bustimes.fields.SecondsField(blank=True, null=True)),
                ('sequence', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('timing_status', models.CharField(blank=True, max_length=3)),
                ('pick_up', models.BooleanField(default=True)),
                ('set_down', models.BooleanField(default=True)),
                ('stop', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='busstops.stoppoint')),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bustimes.trip')),
            ],
            options={
                'ordering': ('id',),
                'index_together': {('stop', 'departure')},
            },
        ),
        migrations.CreateModel(
            name='RouteLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('distance_metres', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('geometry', django.contrib.gis.db.models.fields.LineStringField(srid=4326)),
                ('override', models.BooleanField(default=False)),
                ('from_stop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='link_from', to='busstops.stoppoint')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busstops.service')),
                ('to_stop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='link_to', to='busstops.stoppoint')),
            ],
            options={
                'unique_together': {('service', 'from_stop', 'to_stop')},
            },
        ),
        migrations.AddIndex(
            model_name='route',
            index=models.Index(django.db.models.functions.text.Upper('line_name'), name='route_line_name'),
        ),
        migrations.AlterUniqueTogether(
            name='route',
            unique_together={('source', 'code')},
        ),
        migrations.AlterIndexTogether(
            name='route',
            index_together={('start_date', 'end_date'), ('source', 'service_code')},
        ),
        migrations.AlterUniqueTogether(
            name='calendarbankholiday',
            unique_together={('bank_holiday', 'calendar')},
        ),
        migrations.AlterIndexTogether(
            name='calendar',
            index_together={('start_date', 'end_date')},
        ),
    ]
