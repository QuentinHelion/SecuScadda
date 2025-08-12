from pymodbus.client import ModbusTcpClient
import time
from collections import deque

client = ModbusTcpClient("192.168.1.137", port=502)
client.connect()

simulation_active = False
prev_blanc = False
prev_noir = False
prev_bleu = False
prev_piece = False
detection_queue = deque()

def write_outputs(convoyeur, generateur, blade,
                  slot1_belt=False, slot1_turn=False,
                  slot2_belt=False, slot2_turn=False,
                  slot3_belt=False, slot3_turn=False):
    client.write_coil(0, convoyeur)       # Entry conveyor
    client.write_coil(1, blade)           # Stop blade
    client.write_coil(2, generateur)      # Exit conveyor
    client.write_coil(7, slot1_belt)      # Sorter 1 belt
    client.write_coil(8, slot1_turn)      # Sorter 1 turn
    client.write_coil(5, slot2_belt)      # Sorter 2 belt
    client.write_coil(6, slot2_turn)      # Sorter 2 turn
    client.write_coil(9, slot3_belt)      # Sorter 3 belt
    client.write_coil(4, slot3_turn)      # Sorter 3 turn

# 🧼 Initialisation
write_outputs(False, False, True)

try:
    last_detection_time = 0
    detection_delay = 0.3  # Pour éviter les doublons

    while True:
        # Lecture des boutons
        di = client.read_discrete_inputs(1, 3)
        if di.isError():
            time.sleep(0.5)
            continue

        bouton_blanc = di.bits[0]
        bouton_bleu = di.bits[1]
        bouton_noir = di.bits[2]

        # START
        if bouton_blanc and not prev_blanc and not simulation_active:
            print("✅ START")
            simulation_active = True
            write_outputs(True, True, False)

        # PAUSE
        elif bouton_noir and not prev_noir and simulation_active:
            print("⏸️ PAUSE")
            simulation_active = False
            write_outputs(False, False, True)

        # RESET
        elif bouton_bleu and not prev_bleu:
            print("🔁 RESET")
            simulation_active = False
            detection_queue.clear()
            write_outputs(False, False, True)

        # Lecture capteur vision
        reg = client.read_input_registers(0, 1)
        capteur_id = reg.registers[0] if not reg.isError() else 0

        now = time.time()

        # ➕ Ajout à la queue si pièce détectée
        if simulation_active and capteur_id != 0 and (now - last_detection_time) > detection_delay:
            detection_queue.append(capteur_id)
            last_detection_time = now

        # 🎯 Si une pièce est à traiter (FIFO)
        if simulation_active and detection_queue:
            piece_id = detection_queue.popleft()
            if piece_id in [1, 2, 3]:  # BLEU → Sorter 1
                if prev_piece == False or prev_piece == "blue":
                    write_outputs(True, True, False, slot1_belt=True, slot1_turn=True)
                else:
                    write_outputs(False, True, True, slot2_belt=True, slot2_turn=True)
                    time.sleep(2.5)
                    write_outputs(False, True, False, slot1_belt=True, slot1_turn=True)
                prev_piece = "blue"

            elif piece_id in [4, 5, 6]:  # VERT → Sorter 2
                if prev_piece == False or prev_piece == "green":
                    write_outputs(True, True, False, slot2_belt=True, slot2_turn=True)
                else:
                    write_outputs(False, True, True, slot1_belt=True, slot1_turn=True)
                    time.sleep(4)
                    write_outputs(False, True, False, slot2_belt=True, slot2_turn=True)
                prev_piece = "green"

            elif piece_id in [7, 8, 9]:  # AUTRES → Sorter 3
                print("🟡 Tri AUTRE")
                write_outputs(False, True, False, slot3_belt=True, slot3_turn=True)

        # Mise à jour des états boutons
        prev_blanc = bouton_blanc
        prev_noir = bouton_noir
        prev_bleu = bouton_bleu

        time.sleep(0.05)

except KeyboardInterrupt:
    print("🟥 Arrêt manuel")

finally:
    print("🧼 Extinction sécurisée")
    write_outputs(False, False, False)
    client.close()
