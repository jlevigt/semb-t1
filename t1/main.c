#include <stdio.h>
#include <stdlib.h>
#include <termios.h>
#include <unistd.h>
#include "tests/tests.h"

// ANSI Color Codes
#define CLR_RESET  "\x1b[0m"
#define CLR_HEADER "\x1b[1;36m" // Bold Cyan
#define CLR_MENU   "\x1b[33m"   // Yellow
#define CLR_ERROR  "\x1b[1;31m" // Bold Red
#define CLR_EXIT   "\x1b[1;32m" // Bold Green
#define CLR_WAIT   "\x1b[5;37m" // Blinking Gray

void clear_terminal() {
    printf("\033[H\033[J");
}

char get_instant_char() {
    char buf = 0;
    struct termios old = {0};
    if (tcgetattr(0, &old) < 0) perror("tcsetattr()");
    old.c_lflag &= ~ICANON;
    old.c_lflag &= ~ECHO;
    old.c_cc[VMIN] = 1;
    old.c_cc[VTIME] = 0;
    if (tcsetattr(0, TCSANOW, &old) < 0) perror("tcsetattr ICANON");
    if (read(0, &buf, 1) < 0) perror("read()");
    old.c_lflag |= ICANON;
    old.c_lflag |= ECHO;
    if (tcsetattr(0, TCSADRAIN, &old) < 0) perror("tcsetattr ~ICANON");
    return buf;
}

void wait_for_keypress() {
    printf("\n" CLR_WAIT "Press any key to return to menu..." CLR_RESET);
    fflush(stdout);
    get_instant_char();
}

void print_menu() {
    clear_terminal();
    printf(CLR_HEADER "==============================\n");
    printf("   ChaCha20 Didactic TUI\n");
    printf("==============================\n" CLR_RESET);
    printf(CLR_MENU "1." CLR_RESET " Demo Basic Encryption\n");
    printf(CLR_MENU "2." CLR_RESET " Run RFC 8439 Test Vectors\n");
    printf(CLR_MENU "3." CLR_RESET " Demo Nonce Reuse Vulnerability\n");
    printf(CLR_MENU "4." CLR_RESET " Test with 8KB of data\n");
    printf(CLR_MENU "5." CLR_RESET " Test with Custom User Input\n");
    printf(CLR_MENU "6." CLR_RESET " Test with OpenSSL version\n");
    printf(CLR_MENU "0." CLR_RESET " Exit\n");
    printf("\nSelection: ");
    fflush(stdout);
}

int main() {
    while (1) {
        print_menu();
        char choice = get_instant_char();
        printf("%c\n", choice); // Echo the choice

        switch (choice) {
            case '1':
                clear_terminal();
                demo_encrypt();
                wait_for_keypress();
                break;
            case '2':
                clear_terminal();
                test_vectors();
                wait_for_keypress();
                break;
            case '3':
                clear_terminal();
                demo_nonce_reuse();
                wait_for_keypress();
                break;
            case '4':
                clear_terminal();
                test_8kb();
                wait_for_keypress();
                break;
            case '5':
                clear_terminal();
                // If the user inputs text, we need to be careful with terminal state
                test_user_input();
                wait_for_keypress();
                break;
            case '6':
                clear_terminal();
                // If the user inputs text, we need to be careful with terminal state
                test_openssl();
                wait_for_keypress();
                break;
            case '0':
                printf(CLR_EXIT "\nExiting safely. Goodbye!\n" CLR_RESET);
                return 0;
            default:
                printf(CLR_ERROR "\nInvalid option '%c'. Try again.\n" CLR_RESET, choice);
                sleep(1);
        }
    }
}
