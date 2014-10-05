from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from account import views

urlpatterns = patterns(
    '',
    url(
        r'^profile/$',
        views.ProfileView.as_view(),
        name='profile'
    ),

    url(
        r'^signup/$',
        views.Signup.as_view(),
        name='signup'
    ),
    url(
        r'^activate/resend/$',
        views.ActivationResend.as_view(),
        name='activate_resend'
    ),
    url(
        r'^activate/(?P<activation_key>\w+)/$',
        views.Activation.as_view(),
        name='activate'
    ),
    url(
        r'^activate/retry/(?P<activation_key>\w+)/$',
        views.ActivationRetry.as_view(),
        name='activate_retry'
    ),
    url(
        r'^signin/$',
        views.Signin.as_view(),
        name='signin'
    ),
    url(
        r'^signout/$',
        views.Signout.as_view(),
        name='signout'
    ),
    url(
        r'^email/$',
        views.Email_Change.as_view(),
        name='email_change'
    ),
    url(
        r'^confirm-email/(?P<confirmation_key>\w+)/$',
        views.EmailConfirm.as_view(),
        name='email_confirm'
    ),
    url(
        r'^password/reset/$',
        views.PasswordReset.as_view(),
        name='password_reset'
    ),
    url(
        r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        views.PasswordResetConfirm.as_view(),
        name='password_reset_confirm'
    ),
    url(
        r'^password/$',
        views.PasswordChange.as_view(),
        name='password_change'
    ),
    url(
        r'^test/$',
        views.Test.as_view(),
        name='test'
    )
)

urlpatterns = format_suffix_patterns(urlpatterns)
