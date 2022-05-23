# Generated by Django 4.0.4 on 2022-05-23 18:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_de_usuarios', '0002_usuario_de_riesgo'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='inscripcion',
            options={'verbose_name_plural': 'Inscripciones'},
        ),
        migrations.AlterModelOptions(
            name='usuario',
            options={'verbose_name_plural': 'Usuarios'},
        ),
        migrations.AlterModelOptions(
            name='vacunaaplicada',
            options={'verbose_name_plural': 'Vacunas_aplicadas'},
        ),
        migrations.AlterModelOptions(
            name='vacunador',
            options={'verbose_name_plural': 'Vacunadores'},
        ),
        migrations.RenameField(
            model_name='usuario',
            old_name='es_adm',
            new_name='es_administrador',
        ),
        migrations.RemoveField(
            model_name='usuario',
            name='contrasenia',
        ),
        migrations.AddField(
            model_name='usuario',
            name='_is_superuser',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usuario',
            name='es_vacunador',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usuario',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last login'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='password',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='vacuna',
            name='inscriptos',
            field=models.ManyToManyField(blank=True, default=None, null=True, related_name='campañas_inscriptas', through='gestion_de_usuarios.Inscripcion', to='gestion_de_usuarios.usuario'),
        ),
        migrations.AddField(
            model_name='vacuna',
            name='tienen_aplicaciones',
            field=models.ManyToManyField(blank=True, default=None, null=True, related_name='vacunas_aplicadas', through='gestion_de_usuarios.VacunaAplicada', to='gestion_de_usuarios.usuario'),
        ),
        migrations.AddField(
            model_name='vacunatorio',
            name='vacunas_en_stock',
            field=models.ManyToManyField(blank=True, default=None, null=True, related_name='vacunatorios_con_stock', through='gestion_de_usuarios.VacunaVacunatorio', to='gestion_de_usuarios.vacuna'),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='dni',
            field=models.CharField(max_length=8, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='vacunador',
            name='usuario',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='gestion_de_usuarios.usuario'),
        ),
        migrations.AlterUniqueTogether(
            name='inscripcion',
            unique_together={('usuario', 'vacuna')},
        ),
        migrations.AlterUniqueTogether(
            name='vacunavacunatorio',
            unique_together={('vacuna', 'vacunatorio')},
        ),
    ]
