{% if setup_callback %}{{ setup_callback }}(JSON.parse('{{ config|safe }}'));{% else %}converse.initialize(JSON.parse('{{ config|safe }}'));{% endif %}
