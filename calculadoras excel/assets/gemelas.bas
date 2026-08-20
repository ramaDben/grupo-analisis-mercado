Option Explicit

' ---------------------------------------------------------------------------
' Simulador GI · sincronizacion de las columnas gemelas
'
' VOLUMEN EN CLP (D) y VOLUMEN EN LOTES (E) son la misma magnitud en dos
' unidades. Se escribe en cualquiera de las dos y la otra se recalcula.
'
' Este codigo va en el modulo de la HOJA "Simulador" (no en un modulo estandar):
' en el editor de VBA, Microsoft Excel Objetos -> Simulador. Usa Me, que solo
' existe en el modulo de hoja.
'
' Por que hace falta una macro: dos celdas no pueden ser a la vez editables y
' calculadas. Si cada una fuera formula de la otra, Excel entra en referencia
' circular, y no hay forma de saber cual se edito de ultimo sin capturar el
' evento de cambio.
'
' Equivalencia: los lotes que ocupa un importe salen de dividirlo por el margen
' que exige un lote a ese precio, que es precio_entrada x clp_unidad x tasa.
' clp_unidad y tasa los resuelve la hoja en P4 y P5 segun el instrumento elegido.
'
' El paso minimo de volumen que acepta MT5 es 0,01 lotes, asi que el volumen se
' trunca a ese paso y el importe se homologa al equivalente exacto del volumen
' resultante. El importe que se escribio puede por lo tanto ajustarse a la baja:
' es deliberado, para que las dos columnas digan lo mismo y para que el margen
' requerido del cierre sea el real y no el pretendido.
' ---------------------------------------------------------------------------

Private Const F_INI As Long = 11          ' primera fila de operacion
Private Const F_FIN As Long = 16          ' ultima fila de operacion
Private Const COL_CLP As Long = 4         ' D · VOLUMEN EN CLP
Private Const COL_LOTES As Long = 5       ' E · VOLUMEN EN LOTES
Private Const COL_ENTRADA As Long = 6     ' F · PRECIO DE ENTRADA
Private Const PASO As Double = 0.01       ' volumen minimo de MT5

Private Sub Worksheet_Change(ByVal Target As Range)
    Dim vigilado As Range, comun As Range, celda As Range

    ' el evento se limita a las tres columnas implicadas: editar cualquier otra
    ' parte de la hoja no ejecuta nada
    Set vigilado = Me.Range(Me.Cells(F_INI, COL_CLP), Me.Cells(F_FIN, COL_ENTRADA))
    Set comun = Application.Intersect(Target, vigilado)
    If comun Is Nothing Then Exit Sub

    ' sin esto, escribir la celda gemela volveria a disparar el evento
    Application.EnableEvents = False
    On Error Resume Next
    For Each celda In comun
        Sincronizar celda.Row, celda.Column
    Next celda
    On Error GoTo 0
    Application.EnableEvents = True
End Sub

Private Function Numero(v As Variant) As Double
    ' las celdas vacias y el texto valen cero, no error
    If IsNumeric(v) Then Numero = CDbl(v) Else Numero = 0
End Function

Private Function Truncar(lotes As Double) As Double
    ' hacia abajo al paso de 0,01. El epsilon evita que 0,54 caiga a 0,53 por
    ' la representacion binaria del numero
    Truncar = Int(lotes / PASO + 0.000001) * PASO
End Function

Private Sub Sincronizar(fila As Long, columna As Long)
    Dim margenPorLote As Double, lotes As Double, pesos As Double

    margenPorLote = Numero(Me.Cells(fila, COL_ENTRADA).Value) _
                  * Numero(Me.Range("P4").Value) _
                  * Numero(Me.Range("P5").Value)

    ' sin precio de entrada no hay equivalencia posible: se deja tal cual y la
    ' franja de validacion de la hoja lo advierte
    If margenPorLote <= 0 Then Exit Sub

    Select Case columna

        Case COL_LOTES                                   ' se escribio el volumen
            lotes = Truncar(Numero(Me.Cells(fila, COL_LOTES).Value))
            If lotes <= 0 Then
                Me.Cells(fila, COL_LOTES).ClearContents
                Me.Cells(fila, COL_CLP).ClearContents
            Else
                Me.Cells(fila, COL_LOTES).Value = lotes
                Me.Cells(fila, COL_CLP).Value = lotes * margenPorLote
            End If

        Case COL_ENTRADA                                  ' cambio el precio
            ' manda el volumen en lotes: se actualiza solo su equivalente en pesos
            lotes = Truncar(Numero(Me.Cells(fila, COL_LOTES).Value))
            If lotes > 0 Then Me.Cells(fila, COL_CLP).Value = lotes * margenPorLote

        Case COL_CLP                                      ' se escribio el importe
            pesos = Numero(Me.Cells(fila, COL_CLP).Value)
            If pesos <= 0 Then
                Me.Cells(fila, COL_LOTES).ClearContents
                Exit Sub
            End If
            lotes = Truncar(pesos / margenPorLote)
            Me.Cells(fila, COL_LOTES).Value = lotes
            If lotes > 0 Then
                Me.Cells(fila, COL_CLP).Value = lotes * margenPorLote
            End If
            ' si el importe no alcanza ni al volumen minimo, se deja escrito tal
            ' cual: asi la franja de validacion puede avisarlo, en vez de que el
            ' numero desaparezca sin explicacion

    End Select
End Sub
