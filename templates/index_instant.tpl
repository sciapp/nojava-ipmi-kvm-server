{% extends 'index.tpl' %}
{% block ws_onopen %}

document.getElementById('kvm-server').value = {% raw server_name %};
document.getElementById('kvm-password').value = {% raw password %};
document.getElementById('kvm-resolution').value = {% raw resolution %};

start_kvm();

{% end %}
