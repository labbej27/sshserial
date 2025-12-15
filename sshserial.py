import asyncio
import paramiko
import serial

# --- SSH configuration ---
SSH_HOST = "ip serveur ssh"  # à adapter
SSH_USER = "minitel"
SSH_PORT = 22
SSH_PASSWORD = "password"  # à adapter 

# --- Serial / Minitel configuration ---
SERIAL_TTY = "/dev/cu.usbserial-130"   # à adapter (j'étais sur macOS et magis club)
SERIAL_SPEED = 9600          # ou 1200 si Minitel 1
async def main():
    # --- Open serial port ---
    ser = serial.Serial(
        SERIAL_TTY,
        SERIAL_SPEED,
        parity=serial.PARITY_NONE, # PARITY_EVEN si Minitel 1
        bytesize=8, # serial.STOPBITS_ONE, si Minitel 1
        timeout=2
    )

    # --- Open SSH ---
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        SSH_HOST,
        port=SSH_PORT,
        username=SSH_USER,
        password=SSH_PASSWORD
    )

    chan = client.invoke_shell(
        term='m1b',
        width=40,
        height=24
    )

    chan.send("stty -ixon\n")

    # --- Init Minitel ---
    ser.write(b'\x07\x0c\x1f\x40\x41connexion\x0a')
    # disable local echo
    ser.write(b'\x1b\x3b\x60\x58\x52')

    async def serial_to_ssh():
        """Minitel -> SSH"""
        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                try:
                    chan.send(data.decode("latin1", errors="ignore"))
                except Exception:
                    pass
            await asyncio.sleep(0.01)

    async def ssh_to_serial():
        """SSH -> Minitel"""
        while True:
            if chan.recv_ready():
                data = chan.recv(1024)
                ser.write(data)
            await asyncio.sleep(0.01)

    await asyncio.gather(serial_to_ssh(), ssh_to_serial())

if __name__ == "__main__":
    asyncio.run(main())
