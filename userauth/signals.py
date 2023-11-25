# # signals.py
# # from django.db.models.signals import post_save
# # from django.dispatch import receiver
# # from django.contrib.auth.models import User
# # from .models import UserProfile
# from django.core.mail import send_mail
# # from django.http import HttpResponse
# # from django.utils import timezone
# # import random
# # import string


# # @receiver(post_save, sender=User)
# # def create_user_profile(sender, instance, created, **kwargs):
# #     if created and not instance.is_staff:
# #         UserProfile.objects.create(user=instance)

# # @receiver(post_save, sender=User)
# # def send_email_token(sender, instance, created, **kwargs):
# #     try:
# #         if created and not instance.is_staff:
# #             email_token = generate_random_string(6)
# #             user_profile = instance.userprofile
# #             user_profile.otp = email_token
# #             user_profile.email_token_created_at = timezone.now()
# #             user_profile.save()
# #             send_otp_email(instance.email, email_token, instance.first_name)
# #     except Exception as e:
# #         print(e)
# #         return HttpResponse(e)
        

# def send_otp_email(email, otp, username):
#     subject = "JERSEY CITY OTP AUTHENTICATION"
#     message = f"{otp} - OTP"
#     from_email = "dinilkrishna594@gmail.com"
#     recipient_list = [email]
#     send_mail(subject, message, from_email, recipient_list, fail_silently=False)

