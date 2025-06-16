import os
import rsa
import sys
import base64
import random
import tkinter as tk
import tkinter.messagebox
def generate_mapping_for_base64_characters(seed=0, max_index=10000):
    random.seed(seed)
    base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=Ο"
    mapping = {}
    for index in range(max_index):
        for char in base64_chars:
            while True:
                mapped_code = random.randint(0, 0x10FFFF)
                if not (0xD800 <= mapped_code <= 0xDFFF):
                    break
            mapping[(char, index)] = chr(mapped_code)
    return mapping
def generate_decryption_mapping(encryption_mapping):
    decryption_mapping = {}
    for (char, index), mapped_char in encryption_mapping.items():
        decryption_mapping[(mapped_char, index)] = char
    return decryption_mapping
def complex_encrypt(text,seed=0 ):
    mapping = generate_mapping_for_base64_characters(seed,len(text))
    encrypted_text = ""
    for index, char in enumerate(text):
        encrypted_text += mapping.get((char, index), char)
    return encrypted_text
def complex_decrypt(text, seed=0):
    mapping=generate_decryption_mapping(generate_mapping_for_base64_characters(seed,len(text)))
    decrypted_text = ""
    for index, char in enumerate(text):
        decrypted_text += mapping.get((char, index), char)
    return decrypted_text
try:
    Public='LS0tLS1CRUdJTiBSU0EgUFVCTElDIEtFWS0tLS0tΟTUlJQ0NnS0NBZ0VBaWJHdjdtSEg5UmJ6TUw0V0tORFRCTGFFZXNTWXVEQzQ4VFdZeDgxZ1dRNFBjΟTXkzU0RvMg==ΟMmRROG0vTjlKY25vTSt4VjNPbHZLRDNwTHdhQ2Y1UjFIb09vcyt3Y1Mva2JRUllFZTJSbmZleWg1ΟN3BHdktMWg==ΟUTduRDFKcjVYQjRPamM0emxjM0s2US9IdlNSaEJmUklSYytSTmpMcWpKaG1vRlFUM2VIU3NNSVhRΟM0xxUlBDRg==ΟYTByazNhdVJEUktkdmNTVU1YU0JnbnhOeStUUXZCZkZjbDNNZ2Y2em5qUndkRGYvV2JsZWN1UnJ3ΟcFZaWGw3RA==ΟV0JYR2hPOElHL0JUZzZnNkN5MXdaL1RQYm1lVnRRZnRtVG5Tc1VzU05OaHB0a0YxZjVQK2lQUmFYΟLzJvMWF4MQ==ΟRnM3bUJCTHZBWUwzSzg3aFdiUXMzUEQwWkRhN0ZwOGs1bFdhUklVT01pTkJvQm94SUlKQ0JnOGZnΟUnFlZy9pdg==ΟUjVwQ1VyNlZramR6RS9UVHdWaGpqM25PWnJaaDkzOGNTTkxUOUQ3L3YvRTNVSkd5cVhrZThUOENqΟRzVRMGxJcQ==ΟTDRNVE5LNm5qVXZ1ZDhLbXZuNUZHTWlteDM3eEprV3BpallNb3VVUmlMT3JiL2lvKzlzSGhTMXYrΟMEh0dEVKUA==ΟaUs0K0RaRU1JVTRNeHhlQll0b1BDWmZ2cVk0SkFHeTlBKzVUY0owcEF4dUN1aTNDWjBMZFNYOVQwΟKzV6UzRIRg==ΟZDgraXloVjBQMk9ORnRudFl1ci85VVRwdktNOWdDOTcxZTFVKzFJdFhETnZSU05sL0pMcjdrdFZTΟUCtUY1F3Vw==ΟSnZ3OS85a0IyZFBmZ0kvWFdzTHdONFNrOEcrNGlzWk93c2NkNUlnblJPY1BXcEtuQ1BzV1Aya0NBΟd0VBQVE9PQ==ΟLS0tLS1FTkQgUlNBIFBVQkxJQyBLRVktLS0tLQ=='
    Private=' LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQ==ΟTUlJSk53SUJBQUtDQWdFQWliR3Y3bUhIOVJiek1MNFdLTkRUQkxhRWVzU1l1REM0OFRXWXg4MWdXΟUTRQY015Mw==ΟU0RvMjJkUThtL045SmNub00reFYzT2x2S0QzcEx3YUNmNVIxSG9Pb3Mrd2NTL2tiUVJZRWUyUm5mΟZXloNTdwRw==ΟdktMWlE3bkQxSnI1WEI0T2pjNHpsYzNLNlEvSHZTUmhCZlJJUmMrUk5qTHFqSmhtb0ZRVDNlSFNzΟTUlYUTNMcQ==ΟUlBDRmEwcmszYXVSRFJLZHZjU1VNWFNCZ254TnkrVFF2QmZGY2wzTWdmNnpualJ3ZERmL1dibGVjΟdVJyd3BWWg==ΟWGw3RFdCWEdoTzhJRy9CVGc2ZzZDeTF3Wi9UUGJtZVZ0UWZ0bVRuU3NVc1NOTmhwdGtGMWY1UCtpΟUFJhWC8ybw==ΟMWF4MUZzN21CQkx2QVlMM0s4N2hXYlFzM1BEMFpEYTdGcDhrNWxXYVJJVU9NaU5Cb0JveElJSkNCΟZzhmZ1JxZQ==ΟZy9pdlI1cENVcjZWa2pkekUvVFR3VmhqajNuT1pyWmg5MzhjU05MVDlENy92L0UzVUpHeXFYa2U4ΟVDhDakc1UQ==ΟMGxJcUw0TVROSzZualV2dWQ4S212bjVGR01pbXgzN3hKa1dwaWpZTW91VVJpTE9yYi9pbys5c0hoΟUzF2KzBIdA==ΟdEVKUGlLNCtEWkVNSVU0TXh4ZUJZdG9QQ1pmdnFZNEpBR3k5QSs1VGNKMHBBeHVDdWkzQ1owTGRTΟWDlUMCs1eg==ΟUzRIRmQ4K2l5aFYwUDJPTkZ0bnRZdXIvOVVUcHZLTTlnQzk3MWUxVSsxSXRYRE52UlNObC9KTHI3Οa3RWU1ArVA==ΟY1F3V0p2dzkvOWtCMmRQZmdJL1hXc0x3TjRTazhHKzRpc1pPd3NjZDVJZ25ST2NQV3BLbkNQc1dQΟMmtDQXdFQQ==ΟQVFLQ0FnQUNHbVd1aFczUmI0Vk5aRW5nVzdndFpVQkd3OFAxWkVFZTVndXNXWlcwSm9QVDNEeWNiΟTTh6cW9zMg==ΟY3BTaHhDQzQwazVKYm9OVklRVHp3K3l3V0NzbHlTc0ZmSUMrSkZMblBwZlk3cUtxQ0xnOFd0c0R2ΟSlVHOU1wcA==ΟNytnSklTaGx3QldIbnpvUEx6K0V3dzU4VWN2Y3pSdlJzUnRtQkZuazd3UFNxc1ZXRDlEZEpkOHdLΟR0JSVURhSQ==Οc0RzcDhQUFoxeXZRU1pCRTF2TTFQd3gxSXdQUUNHQzhSNUNreFBaR3dDZzFUYUNFcnJwNm9WOVpFΟcWQzSy9YNQ==ΟUjlGZTQ5L1NyZm9jKzVldzdzdFFTMks4L2g4QjdTRXJ0aExVSGM0WGk0NW80WERNMUxhZ3FyWXVkΟVkRnaFU1OA==ΟRjNIeEd2ZjYySkdlNG9xQnR4NmdFdTJRSm9MU0g3WE9MWWV4NCtwbGpzWVBXMW15Y0sxTCsrZVFWΟeXFoVXFKbg==ΟVGhCa0MwWVZRSjR4L0dRL0pJN3I1dU1GRGNORnpJWHJGWFAvQVNoVHNhU1RCN2FSamNHc3c3SXhNΟZ1dJUmljQg==Οdi9uU2dPWmpFeHlZVVFWbGpHYmdkNlZXZEJRYm9tU1k3OXFpdy96L2l1Y0tVaXhpaU93eEhGMm5iΟa09mNWNubA==ΟRUY3WHozRTRETURZZy9sQ3QrY0xqd29WdDVOeGtnZjRiQ3ZwWjU4QzE1RjdickdhSkJIaTU2dU1RΟMnUzcFNrOQ==ΟQ2ZNTjJqUm1RZ3RTU0t3M3ZUNmhPbzBvaVZLdXdNNDgxZVNxMDZVcEFXTDBSN1RCZjJXdGJtM2J2ΟdXU4eDYrKw==Οd0NCZ2VqeUJaUTd0OUl1SUVQMjV2RVo4cmxOUUUwSm9idkR5Wk90eG9DMVNZT0pyNVFLQ0FSRUFyΟbHBsdGJyNg==ΟN1dlSWF2bzJWa2gwUmhwSnZLSStLeE9WSWZvUTNxMTNCQ3VPTVM5NGtlQ2t1cVV5QURKVzZvTFBmΟdGFqVEg1Vw==ΟcnlUMUFHeGEvS0FMSWdQODRxUVlXN2kwZzh3azh2c1hMN21JUk1NMWMvYVZtanFnWEM1T2pHT0RuΟRXp0OFVFOA==ΟYWp5RGhIT2NWQlJRZnVFYmRDb05iNGd6NlBZeUE5MmRvOXhqN2RNWHFYRlQrejZIRGl5anZaZmFUΟWjVsTHQrRg==ΟYTV3cEZBeE5kcWc2cVh1YkJMb3pFMlZKMU5ZZVRKQ0xyNTRWQXl0cERsaEEzQW81enpnZmFMSFhaΟZDZ4SE9oTw==ΟenVLcXBKTVV4UXV0VSs1dmJFN2ZSNExockZEN0huaXdCcTRsT0hSeTNFOHNNWjRzRXJGTHpLRDhDΟTWVUc1R4Zg==ΟMzV3aUZwWG9Vazkyb3c5WFhtYmEzcEhUbjV5Mk1yNmRkRU1DZ2ZFQXlpeVRDRGQ0TldQNGRWdGhHΟZzVZU0djcA==ΟRW1GRDNuTXR0REx2QUpuLytYcStpM2dRUlNIeGxjTlJIdzhwZTBpNkdqNGNhYWR5SjlEenViWThiΟZG9iRlRCKw==Οd2VZa3o4TE5mOS93QkR4NTFldS9SYi9ndUQxVGJHVUZZbk8zS0wxdkNmOTY2bzNIUUF6eWRBZkRrΟWVNoTi9tYg==ΟcVkrVXp3Q291Q1QxS2hUNnI1VWwyOXFXYUZ6SFFER3BaWEpmTVd0ckZhV25qejR4YzNUdDJQSGRrΟRGpWY3hSYQ==ΟT1dCYWlpdmtVMjYyeml6U3JnSkJJd2R2V3pJRk5UTGxXbFJYMi9MVDMwc1U1am9CVkd5eERYZUxyΟTEMzNFVLeQ==ΟOUdERjNTcUNBc3NFZHp1VXhKVzVzcWVMRkU1VHZZSklUY2tqK0xqakFvSUJFSGVmQmRGZGEvT2Q2ΟUGFjbk5NdA==ΟK3JodUtORUc3MmhXa3ljd2pvcDRzUU5uYnJOSVFveXpkOUdtclZ0OUxpelBldFVuSmZyQlkyL2ZCΟMGszRG1Ycw==ΟMkRhS1RlS2hleVRTNE9iY0ZTMndJQVJhWXFmcTFxMnRMSThZVWhWc24rK3FCdzRocWM2d1YyYjhCΟYS9HTWlkdA==ΟbUp5MGpVVng1SzMwNE1pZ3dVZnRzTTVQMHkvRWVLT0VZWDRyTkRZQllvWWR2V1VybTNoQld5U3RpΟM0Y1ejF2dA==ΟcC9ISUlGOXA4TWtKNFZIcFpmaFo0N3lsMVB6THQ5UmpzSHhIZDhvNFV6UmRiODh3cm91S3h5Y2lWΟTGw5UCs3Qg==ΟU0RZaGpNamVoRXBuL2JWZ0NpcXAydnQ2VjRjWVBnWHhPL3orN0hZV3RrNjYxTENoWFM5b29NNm1MΟSzBhUkw3VQ==ΟVGkwcHhXTzdaY2IyZmg4d1FjRW5EcGhKQW9IeEFKbG03djE2RVVUNW9PbHpONTlzcVFIdS9KUU1wΟMUdmdFZzWQ==ΟbG82dlN6SENOOWhkZG9MdU9YKzRYdEloVUFsU2FwdEU2NHdqV0pQcmtUTWxtbjZEMHE3bVNCZmFCΟNjU1RWpKbg==ΟK1pkTlIralFZeWFLYS9sLzFzL1ZheHVEejhNaTBhRVZiKytQT2xOWVA1TlkzTVNLalVXS3FOa2tyΟL1hOZXplVw== ΟRzB3ZDlRVExONW0xSnhEeTdPREJqZFlDelVZVFNvSjNXa2R2R2xpUHJYVkNPQ3FaWlNSWG1nb1ZHΟVDNrQmZCaw==ΟZm1LOFVmTmtsSVgrdXpqSUlIbDRMOXkxU0tFRWhFeldqSG9RSXpncTdNRGFKMm9XQUwvME94TUFaΟc0hrNGhjNg==ΟY2g0Q1lHUTFjMXlpa2Y0TFhMRGJyUDhRa3JIRG53S0NBUkVBa0FzM3lIeStKNGlQVU9DVGZWT29yΟQmVNUm5xUw==ΟMjVhYzZiS1RCQkJCQmRwTnh6eFl2RE04N2IzRi9GSTBIUmNaQkxpT3ZQck10UWxTV25IeDVUS3NVΟcWRuZkdMeA==ΟY3I1UXl1Z0VxNmp2ZHhuelpRN2JNK04rQ0JwUFVpNkdhZFNMcVhYMG0yemNsTXhKdU0wY1BzMTFsΟeEREMGIwVw==ΟOWxQNkxMU200M3pMRlhhL3d6SFQ4bGsvZ0lEaTh1WEpUL3Z2M2JwdUt3VE9VYnF1SE1hWjBSeUYxΟQjRoMXVGTg==ΟeHJCSGdDY1J3OTA4RlUwaXptcFB3cldqMW1ydXYzSDhjcm1HUFF6bGovKzdnV0FBWkJrNm5rcHVuΟMnVRK0JxVg==ΟbEo1S29Xam0ySDdDMmlDUGlWM1lQUnI4NjJkZ1dHVlhFVklrUFlBanB3NzVLdW1BT1ZpQ2lCRmNWΟTldYU1RZVw==ΟQ3FrVFhJSGZiWFg0L2lVPQ==ΟLS0tLS1FTkQgUlNBIFBSSVZBVEUgS0VZLS0tLS0=򕂝񣨖񺥋󞼡-𡾓񣴹-򽃲𫩱'
except Exception as e:
    root = tk.Tk()
    root.withdraw()
    tk.messagebox.showerror('Error','No License.')
    sys.exit(0)
def Encrypt(Item,Public):
    PublicKey=rsa.PublicKey.load_pkcs1(b'\n'.join([base64.decodebytes(i.encode()) for i in Public.split('Ο')]))
    return base64.encodebytes(rsa.encrypt(Item.encode(),PublicKey)).decode('UTF-8').strip().replace('\n','ο')
def Decrypt(Item,Private):
    PrivateKey=rsa.PrivateKey.load_pkcs1(b'\n'.join([base64.decodebytes(i.encode()) for i in Private.split('Ο')]))
    return rsa.decrypt(base64.decodebytes(Item.encode()),PrivateKey).decode('UTF-8')
