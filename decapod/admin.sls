{% set admin_container_id = salt['cmd.run']("docker ps |grep decapod_admin|awk '{print $1}'") %}
{% if admin_container_id != '' %}
apply_migrations:
  cmd.run: 
    - name: docker exec {{ admin_container_id }} decapod-admin migration apply
{% endif %}
