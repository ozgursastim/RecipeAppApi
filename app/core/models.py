from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
                                        PermissionsMixin


class UserManager(BaseUserManager):
    """ We create our UserManager class extend from BaseUserManager"""
    """ We add '**extra_fields' fields that provide us pass extra fields for this function"""
    """ We do that for flexible function """
    def create_user(self, email, password=None, **extra_fields):
        """ Create and save a new user """
        if not email:
            raise ValueError('Users must have email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """ Creates and saves a new super user """
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """ Custom user model that supports using email instead of username """
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    """ For creating a new user manager for our object """
    objects = UserManager()

    """ By default the username field is
        username and we're customizing that to email
        so we can use an email address. """
    USERNAME_FIELD = 'email'
