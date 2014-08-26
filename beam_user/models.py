from django.db import models

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# See Customizing authentication in Django
# https://docs.djangoproject.com/en/1.6/topics/auth/customizing/


class BeamUserManager(BaseUserManager):

    def _create(self, email, password, first_name, last_name, is_admin):

        if not email:
            raise ValueError('Users must have an email address')

        if not password:
            raise ValueError('Users must have a password')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, first_name, last_name):

        return self._create(email, password, first_name, last_name, True)

    def create_user(self, email, password, first_name, last_name):

        return self._create(email, password, first_name, last_name, False)


class BeamUser(AbstractBaseUser):

    # overwrite abstract property of superclass
    class Meta(AbstractBaseUser.Meta):
        abstract = False

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name')

    # attributes
    email = models.EmailField(
        'Email',
        max_length=30,
        unique=True,
        help_text='Unique Email Address identifying a User'
    )

    first_name = models.CharField(
        'First Name',
        max_length=35,
        help_text='First Name of the User'
    )

    last_name = models.CharField(
        'Last Name',
        max_length=35,
        help_text='Last Name of the User'
    )

    is_active = models.BooleanField(
        default=True
    )

    is_admin = models.BooleanField(
        default=False
    )

    objects = BeamUserManager()

    def get_short_name(self):
        return self.email

    def get_full_name(self):
        return self.get_full_name()

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return True

    @property
    def is_staff(self):
        return self.is_admin

    def save(self, *args, **kwargs):
        self.set_password(self.password)
        super(BeamUser, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()
