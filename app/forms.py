# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import forms
#from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User


#class EditForm(UserChangeForm):

class EditForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "",                
                "class": "form-control"
                
            }
        ))
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder" : "",                
                "class": "form-control"
                
            }
        ))

    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "",                
                "class": "form-control"
            }
        ))

    last_name = forms.CharField(
    widget=forms.TextInput(
        attrs={
            "placeholder" : "",                
            "class": "form-control"
        }
    ))


    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        
