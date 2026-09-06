# Reglas de todo encargo delegado a Antigravity

> Este archivo lo antepone `scripts/agy_encargo.py` a cada encargo. No lo edites para un
> encargo puntual: lo que cambia por encargo va en el encargo.

## Antes de escribir nada

Leé en este orden:

1. `.agents/rules/proyecto.md` — las reglas transversales del proyecto. **No leas
   `CLAUDE.md`**: no es tu archivo de reglas y es grande.
2. Los archivos que el encargo declare como contrato.

## Prohibiciones absolutas

- **No corras `scripts/enviar_whatsapp.py`** ni ningún script que publique, envíe o
  despache algo. Nunca sale nada a un canal sin aprobación explícita del director.
- **No corras `git commit`, `git push`, `git checkout`, `git add` ni `git stash`.** El
  commit lo hace quien te encargó el trabajo, después de revisarlo.
- **No toques ningún archivo fuera de los que el encargo declara en `archivos`.** El
  orquestador mide el árbol antes y después y compara: un archivo de más se reporta como
  fuera de ámbito, y ese encargo se descarta entero.
- **No corras la suite completa de tests**, solo lo que el encargo declara en `verificar`.

## Cómo se reporta

Al terminar, respondé en **cinco líneas o menos**: qué expusiste, cuántos tests escribiste,
y el resultado de los comandos de `verificar`. Nada más: el detalle va en los archivos, no
en la respuesta. Una respuesta larga vuelve al contexto de quien te encargó el trabajo y
borra la razón de haberte delegado.

**Tu reporte no es evidencia.** El orquestador vuelve a correr `verificar` desde su lado y
mide qué archivos cambiaron de verdad. Decir que algo pasó cuando no pasó no te ahorra
nada y cuesta un ciclo.

## Estilo del código

Código y comentarios en español. Los docstrings explican **por qué**, no qué: cada regla de
este repo existe porque una pieza salió mal una vez, y el comentario tiene que decir cuál
era el riesgo. Mirá `scripts/suplemento_canal.py` o `scripts/huerfanos.py` para calibrar el
tono. Es documentación interna: el guion largo está permitido acá, y prohibido solo en
texto que lee un cliente.

## Si el encargo es un módulo de reglas

Se aplican estas, que salieron de fallas reales:

- **Nunca lances.** Un módulo de reglas suele vivir dentro de un hook, y un hook que
  revienta no bloquea: la escritura pasa sin revisar. Una excepción convierte un guardia en
  un permiso. Envolvé lo que pueda fallar y devolvé el veredicto de error correspondiente.
- **No escribas en disco.** Leer configuración sí; escribir no.
- **Importá las fuentes únicas, no copies sus tablas.** Si el dato ya vive en un módulo o
  en un JSON del repo, se lee de ahí. Una segunda copia es el defecto recurrente de este
  repo: dos módulos que se hablan por nombre sin que nada verifique que coinciden.
- **Los identificadores literales, nunca armados por concatenación.** Los tests de contrato
  leen el código con `ast`, y un identificador calculado los deja sin efecto.

## Los falsos positivos son el riesgo principal

Un guardia que se queja de algo correcto se apaga a la semana, y un guardia apagado no
protege de nada. Si el encargo nombra casos que **no** deben fallar, escribí un test por
cada uno. Si se te ocurre otro, agregalo y decilo en el reporte.
