/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define CHACHA20_ROUNDS 20
#define CHACHA20_STATE_WORDS 16
#define CHACHA20_BLOCK_BYTES 64

#define CMD_INIT 0x01
#define CMD_DATA 0x02
#define CMD_END  0x03

#define RESP_ACK_INIT 0x81
#define RESP_ACK_DATA 0x82
#define RESP_ACK_END  0x83
#define RESP_ERROR    0xFF
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */
uint32_t chacha_state[CHACHA20_STATE_WORDS];
uint8_t packet_buffer[128]; // Header(2) + Payload(64) + Checksum(1) + margin
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART2_UART_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
static inline uint32_t rotl32(uint32_t x, int n) {
    return (x << n) | (x >> (32 - n));
}

static inline uint32_t load32_le(const uint8_t src[4]) {
    return (uint32_t)src[0] | 
          ((uint32_t)src[1] << 8) | 
          ((uint32_t)src[2] << 16) | 
          ((uint32_t)src[3] << 24);
}

static inline void store32_le(uint8_t dst[4], uint32_t val) {
    dst[0] = (uint8_t)(val & 0xFF);
    dst[1] = (uint8_t)((val >> 8) & 0xFF);
    dst[2] = (uint8_t)((val >> 16) & 0xFF);
    dst[3] = (uint8_t)((val >> 24) & 0xFF);
}

static void quarter_round(uint32_t *a, uint32_t *b, uint32_t *c, uint32_t *d) {
    *a += *b; *d ^= *a; *d = rotl32(*d, 16);
    *c += *d; *b ^= *c; *b = rotl32(*b, 12);
    *a += *b; *d ^= *a; *d = rotl32(*d, 8);
    *c += *d; *b ^= *c; *b = rotl32(*b, 7);
}

static void chacha20_block(const uint32_t input_state[16], uint8_t keystream[64]) {
    uint32_t x[CHACHA20_STATE_WORDS];
    memcpy(x, input_state, sizeof(x));

    for (int i = 0; i < 10; i++) {
        quarter_round(&x[0], &x[4], &x[8],  &x[12]);
        quarter_round(&x[1], &x[5], &x[9],  &x[13]);
        quarter_round(&x[2], &x[6], &x[10], &x[14]);
        quarter_round(&x[3], &x[7], &x[11], &x[15]);
        quarter_round(&x[0], &x[5], &x[10], &x[15]);
        quarter_round(&x[1], &x[6], &x[11], &x[12]);
        quarter_round(&x[2], &x[7], &x[8],  &x[13]);
        quarter_round(&x[3], &x[4], &x[9],  &x[14]);
    }

    for (int i = 0; i < CHACHA20_STATE_WORDS; i++) {
        store32_le(&keystream[i * 4], x[i] + input_state[i]);
    }
}

uint8_t calculate_checksum(uint8_t *data, uint8_t size) {
    uint8_t checksum = 0;
    for (uint8_t i = 0; i < size; i++) {
        checksum ^= data[i];
    }
    return checksum;
}

void send_packet(uint8_t cmd, uint8_t size, uint8_t *payload) {
    uint8_t header[2] = {cmd, size};
    uint8_t checksum = cmd ^ size;
    for (uint8_t i = 0; i < size; i++) {
        checksum ^= payload[i];
    }
    HAL_UART_Transmit(&huart2, header, 2, HAL_MAX_DELAY);
    if (size > 0) {
        HAL_UART_Transmit(&huart2, payload, size, HAL_MAX_DELAY);
    }
    HAL_UART_Transmit(&huart2, &checksum, 1, HAL_MAX_DELAY);
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART2_UART_Init();
  /* USER CODE BEGIN 2 */

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    uint8_t header[2];
    if (HAL_UART_Receive(&huart2, header, 2, 100) == HAL_OK) {
        uint8_t cmd = header[0];
        uint8_t size = header[1];
        uint8_t payload[64];
        uint8_t received_checksum;

        if (size > 64 && cmd != CMD_INIT) {
            // Error: Size too large
            continue;
        }

        if (HAL_UART_Receive(&huart2, payload, size, 1000) == HAL_OK) {
            if (HAL_UART_Receive(&huart2, &received_checksum, 1, 100) == HAL_OK) {
                uint8_t calculated_checksum = cmd ^ size;
                for (uint8_t i = 0; i < size; i++) {
                    calculated_checksum ^= payload[i];
                }

                if (calculated_checksum == received_checksum) {
                    if (cmd == CMD_INIT && size == 48) {
                        // Constants
                        chacha_state[0] = 0x61707865;
                        chacha_state[1] = 0x3320646e;
                        chacha_state[2] = 0x79622d32;
                        chacha_state[3] = 0x6b206574;
                        // Key
                        for (int i = 0; i < 8; i++) {
                            chacha_state[4 + i] = load32_le(&payload[i * 4]);
                        }
                        // Nonce
                        for (int i = 0; i < 3; i++) {
                            chacha_state[13 + i] = load32_le(&payload[32 + i * 4]);
                        }
                        // Counter
                        chacha_state[12] = load32_le(&payload[44]);

                        send_packet(RESP_ACK_INIT, 0, NULL);
                    } else if (cmd == CMD_DATA) {
                        uint8_t keystream[64];
                        chacha20_block(chacha_state, keystream);
                        
                        for (uint8_t i = 0; i < size; i++) {
                            payload[i] ^= keystream[i];
                        }
                        
                        chacha_state[12]++; // Increment block counter
                        
                        send_packet(RESP_ACK_DATA, size, payload);
                    } else if (cmd == CMD_END) {
                        memset(chacha_state, 0, sizeof(chacha_state));
                        send_packet(RESP_ACK_END, 0, NULL);
                    } else {
                        uint8_t err = 0x01; // Unknown CMD
                        send_packet(RESP_ERROR, 1, &err);
                    }
                } else {
                    uint8_t err = 0x02; // Bad Checksum
                    send_packet(RESP_ERROR, 1, &err);
                }
            }
        }
    }
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 38400;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  huart2.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart2.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOA_CLK_ENABLE();

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */