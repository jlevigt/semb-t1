import argparse
import sys
import os

from core.logger import SessionLogger
from tests import test_rfc_vector, test_random_stream, test_roundtrip, test_negative

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu(port, console_log):
    while True:
        clear_screen()
        print("====================================================")
        print("      ChaCha20 STM32 UART Test Orchestrator        ")
        print("====================================================")
        print(f" Port: {port}")
        print("----------------------------------------------------")
        print(" Selecione um teste para executar:")
        print(" [1] Executar TODOS os Testes")
        print(" [2] Validar Vetor de Teste RFC 8439 (Happy Path)")
        print(" [3] Teste de Stream Aleatório (8KB)")
        print(" [4] Teste de Roundtrip (Criptografar/Descriptografar)")
        print(" [5] Testes Negativos (Parâmetros Incorretos)")
        print(" [0] Sair")
        print("----------------------------------------------------")
        
        choice = input(" Escolha: ")
        
        if choice == '0':
            break
            
        logger = SessionLogger("ManualRun", print_to_console=console_log)
        
        try:
            if choice == '1':
                test_rfc_vector.run_test(port, console_log, logger)
                test_random_stream.run_test(port, console_log, logger)
                test_roundtrip.run_test(port, console_log, logger)
                test_negative.run_test(port, console_log, logger)
            elif choice == '2':
                test_rfc_vector.run_test(port, console_log, logger)
            elif choice == '3':
                test_random_stream.run_test(port, console_log, logger)
            elif choice == '4':
                test_roundtrip.run_test(port, console_log, logger)
            elif choice == '5':
                test_negative.run_test(port, console_log, logger)
            else:
                print(" Opção inválida.")
                continue
        except Exception as e:
            print(f" Erro durante a execução: {e}")
        
        input("\n Pressione Enter para continuar...")
        logger.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChaCha20 UART Test Runner")
    parser.add_argument("port", help="Serial port (e.g., /dev/ttyACM0)")
    parser.add_argument("--console", "-c", action="store_false", help="Disable console logging (logs still saved to file)", default=True)
    args = parser.parse_args()
    
    main_menu(args.port, args.console)
