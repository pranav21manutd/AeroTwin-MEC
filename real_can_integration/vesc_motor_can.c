/*
 * =====================================================================================
 *  REAL CAN INTEGRATION: VESC MOTOR CAN DATA RECEIVER (STANDALONE C PROGRAM)
 * =====================================================================================
 *  Extracted specifically for Smart India Hackathon (SIH) real motor CAN connection.
 *  Reads extended CAN frames for VESC ID 39 (CMD_STATUS1, CMD_STATUS4, CMD_STATUS5).
 *  Strips out BMS, LVGL GUI, and display drivers for high-performance telemetry acquisition.
 * =====================================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <string.h>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <sys/socket.h>
#include <linux/if.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <stdint.h>
#include <math.h>
#include <errno.h>
#include <fcntl.h>

#define VESC_ID        39
#define CMD_STATUS1    9
#define CMD_STATUS4    16
#define CMD_STATUS5    27

// Structure to store extracted VESC motor telemetry
typedef struct {
    int32_t  rpm;
    int16_t  motor_current;     // raw (0.1 A)
    int16_t  mosfet_temp;        // raw (0.1 °C)
    int16_t  motor_temp;         // raw (0.1 °C)
    uint16_t input_voltage;      // raw (0.1 V)
    uint8_t  data_updated;
} vesc_motor_data_t;

static int can_socket = -1;
static pthread_t can_tid;
static pthread_mutex_t can_data_mutex = PTHREAD_MUTEX_INITIALIZER;
static volatile vesc_motor_data_t g_motor = {0};
static volatile int running = 1;

// ---------- CAN Filter & Socket Setup ----------
int init_motor_can_socket(const char *ifname)
{
    struct sockaddr_can addr;
    struct ifreq ifr;

    can_socket = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (can_socket < 0) {
        perror("CAN socket creation failed");
        return -1;
    }

    // Filter ONLY extended frames for VESC Motor
    struct can_filter rfilter[1];
    rfilter[0].can_id   = CAN_EFF_FLAG;
    rfilter[0].can_mask = CAN_EFF_FLAG;

    if (setsockopt(can_socket, SOL_CAN_RAW, CAN_RAW_FILTER, &rfilter, sizeof(rfilter)) < 0) {
        perror("CAN filter set failed");
        close(can_socket);
        return -1;
    }

    strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
    if (ioctl(can_socket, SIOCGIFINDEX, &ifr) < 0) {
        perror("ioctl SIOCGIFINDEX failed");
        close(can_socket);
        return -1;
    }

    addr.can_family = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;

    if (bind(can_socket, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind failed");
        close(can_socket);
        return -1;
    }

    // Set non-blocking read
    int flags = fcntl(can_socket, F_GETFL, 0);
    fcntl(can_socket, F_SETFL, flags | O_NONBLOCK);

    printf("[+] CAN socket initialized on interface '%s' (VESC ID %d filter active)\n", ifname, VESC_ID);
    return 0;
}

// ---------- Parsers for VESC Status Frames ----------
static void parse_motor_status1(struct can_frame *frame)
{
    if (frame->can_dlc != 8) return;

    int32_t rpm = ((int32_t)frame->data[0] << 24) |
                  ((int32_t)frame->data[1] << 16) |
                  ((int32_t)frame->data[2] << 8)  |
                  ((int32_t)frame->data[3]);

    int16_t current = (int16_t)((frame->data[4] << 8) | frame->data[5]);

    pthread_mutex_lock(&can_data_mutex);
    g_motor.rpm = rpm;
    g_motor.motor_current = current;
    g_motor.data_updated = 1;
    pthread_mutex_unlock(&can_data_mutex);
}

static void parse_motor_status4(struct can_frame *frame)
{
    if (frame->can_dlc != 8) return;

    int16_t mosfet_temp = (int16_t)((frame->data[0] << 8) | frame->data[1]);
    int16_t motor_temp  = (int16_t)((frame->data[2] << 8) | frame->data[3]);

    pthread_mutex_lock(&can_data_mutex);
    g_motor.mosfet_temp = mosfet_temp;
    g_motor.motor_temp  = motor_temp;
    g_motor.data_updated = 1;
    pthread_mutex_unlock(&can_data_mutex);
}

static void parse_motor_status5(struct can_frame *frame)
{
    if (frame->can_dlc != 8) return;

    uint16_t input_voltage = (frame->data[4] << 8) | frame->data[5];

    pthread_mutex_lock(&can_data_mutex);
    g_motor.input_voltage = input_voltage;
    g_motor.data_updated = 1;
    pthread_mutex_unlock(&can_data_mutex);
}

// ---------- Standalone CAN Receiver Loop Thread ----------
static void *vesc_can_thread(void *arg)
{
    (void)arg;
    struct can_frame frame;

    printf("[*] VESC CAN receiver thread started listening for Extended CAN frames...\n");

    while (running) {
        while (1) {
            int nbytes = read(can_socket, &frame, sizeof(frame));
            if (nbytes < 0) {
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    break; // Buffer empty
                }
                perror("CAN socket read error");
                break;
            }

            if (nbytes != sizeof(struct can_frame)) continue;

            // Process Extended Frames ONLY
            if (frame.can_id & CAN_EFF_FLAG) {
                uint32_t id = frame.can_id & CAN_EFF_MASK;
                uint8_t controller_id = id & 0xFF;
                uint8_t command       = (id >> 8) & 0xFF;

                if (controller_id == VESC_ID) {
                    if (command == CMD_STATUS1) {
                        parse_motor_status1(&frame);
                    } else if (command == CMD_STATUS4) {
                        parse_motor_status4(&frame);
                    } else if (command == CMD_STATUS5) {
                        parse_motor_status5(&frame);
                    }
                }
            }
        }
        usleep(10000); // 10ms loop rate
    }

    return NULL;
}

// ---------- Main Telemetry Printer ----------
int main(int argc, char *argv[])
{
    const char *ifname = (argc > 1) ? argv[1] : "can0";

    printf("=========================================================================\n");
    printf("   REAL CAN MOTOR DATA RECEIVER (SIH PROTOTYPE INTEGRATION)\n");
    printf("=========================================================================\n");

    if (init_motor_can_socket(ifname) < 0) {
        fprintf(stderr, "Failed to initialize CAN interface '%s'. Exiting.\n", ifname);
        return 1;
    }

    if (pthread_create(&can_tid, NULL, vesc_can_thread, NULL) != 0) {
        perror("Failed to create CAN thread");
        close(can_socket);
        return 1;
    }

    printf("[+] Listening for real VESC Motor data. Press Ctrl+C to terminate.\n\n");

    while (running) {
        vesc_motor_data_t snapshot;
        int updated = 0;

        pthread_mutex_lock(&can_data_mutex);
        if (g_motor.data_updated) {
            snapshot = g_motor;
            g_motor.data_updated = 0;
            updated = 1;
        }
        pthread_mutex_unlock(&can_data_mutex);

        if (updated) {
            float current_amp = snapshot.motor_current / 10.0f;
            float voltage_volts = snapshot.input_voltage / 10.0f;
            float motor_temp_c = snapshot.motor_temp / 10.0f;
            float mosfet_temp_c = snapshot.mosfet_temp / 10.0f;
            float power_kw = (voltage_volts * current_amp) / 1000.0f;

            // Output clean JSON format to stdout for easy pipe into Python digital twin backend
            printf("{\"vesc_id\":%d,\"rpm\":%d,\"current_a\":%.1f,\"voltage_v\":%.1f,\"motor_temp_c\":%.1f,\"mosfet_temp_c\":%.1f,\"power_kw\":%.3f}\n",
                   VESC_ID, snapshot.rpm, current_amp, voltage_volts, motor_temp_c, mosfet_temp_c, power_kw);
            fflush(stdout);
        }

        usleep(100000); // Print snapshot every 100ms (10Hz)
    }

    running = 0;
    pthread_join(can_tid, NULL);
    close(can_socket);
    return 0;
}
