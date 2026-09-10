# Makefile for compiling Real VESC Motor CAN program
CC = gcc
CFLAGS = -Wall -Wextra -O2
LIBS = -lpthread

TARGET = vesc_motor_can
SRC = vesc_motor_can.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LIBS)
	@echo "[+] Compiled $(TARGET) successfully!"

clean:
	rm -f $(TARGET)
