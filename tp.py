from pymodbus.client import ModbusTcpClient
import time

client = ModbusTcpClient("192.168.1.137", port=502)
client.connect()

simulation_active = False

# État précédent des boutons pour détecter les pressions uniques
prev_blanc = False
prev_noir = False
prev_bleu = False

def write_outputs(convoyeur, generateur, slot1, slot2, slot3, stop_blade):
    client.write_coil(0, convoyeur)     # ✅ Coil 0 → Entry conveyor
    client.write_coil(1, stop_blade)    # ✅ Coil 1 → Stop blade
    client.write_coil(2, generateur)    # ✅ Coil 2 → Exit conveyor
    client.write_coil(4, slot1)         # ✅ Coil 4 → Sorter 1 belt
    client.write_coil(5, slot2)         # ✅ Coil 5 → Sorter 2 belt
    client.write_coil(6, slot3)         # ✅ Coil 6 → Sorter 3 belt


# 🧼 Initialisation : tout OFF, blade levée
write_outputs(False, False, False, False, False, True)

try:
    while True:
        # Lecture des boutons
        di = client.read_discrete_inputs(1, 3)
        if di.isError():
            time.sleep(0.5)
            continue

        bouton_blanc = di.bits[0]
        bouton_noir = di.bits[2]
        bouton_bleu = di.bits[1]

        # ➕ START → front montant du bouton blanc
        if bouton_blanc and not prev_blanc and not simulation_active:
            print("✅ START")
            simulation_active = True
            write_outputs(True, True, False, False, False, False)  # blade abaissée

        # ⏸️ PAUSE → front montant du bouton noir
        elif bouton_noir and not prev_noir and simulation_active:
            print("⏸️ PAUSE")
            simulation_active = False
            write_outputs(False, False, False, False, False, True)

        # 🛑 RESET → front montant du bouton bleu
        elif bouton_bleu and not prev_bleu:
            print("🔁 RESET")
            simulation_active = False
            write_outputs(False, False, False, False, False, True)  # blade levée

        # Lecture capteur
        reg = client.read_input_registers(0, 1)
        capteur_id = reg.registers[0] if not reg.isError() else 0

        # Si simulation active, gestion des vérins selon capteur
        if simulation_active:
            if 1 <= capteur_id <= 3:
                write_outputs(True, True, True, False, False, False)
            elif 4 <= capteur_id <= 6:
                write_outputs(True, True, False, True, False, False)
            elif 7 <= capteur_id <= 9:
                write_outputs(True, True, False, False, True, False)
            else:
                # Pas de pièce détectée, continuer à rouler
                write_outputs(True, True, False, False, False, False)

        # Mise à jour des états précédents
        prev_blanc = bouton_blanc
        prev_noir = bouton_noir
        prev_bleu = bouton_bleu

        time.sleep(0.1)

except KeyboardInterrupt:
    print("🟥 Arrêt demandé par l'utilisateur")

finally:
    print("🧼 Extinction sécurisée")
    write_outputs(False, False, False, False, False, False)
    client.close()
