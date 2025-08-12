Pour rendre le code malveillant, on peu ajouter ces lignes de code pour générer des mouvements imprévisibles, rapides et non synchronisés des actionneur

```py
    # Tapis ON/OFF aléatoire
    client.write_coil(0, random.choice([True, False]))  # Entry conveyor
    client.write_coil(2, random.choice([True, False]))  # Exit conveyor
    
    # Stop blade ON/OFF ultra rapide
    client.write_coil(1, random.choice([True, False]))
    
    # Tous les trieurs activés aléatoirement
    for coil in [7, 8, 5, 6, 9, 4]:
        client.write_coil(coil, random.choice([True, False]))
```