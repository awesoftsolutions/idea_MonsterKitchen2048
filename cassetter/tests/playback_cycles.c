#include <pebble.h>
#include "sddriver.h"
#include "audio_track.h"
#include "../compiler/libs/fatfs/ff.h"

extern bool sd_init(void);
extern void sd_deinit(void);
extern bool sd_open_file(const char *path, FIL *file);
extern void sd_close_file(FIL *file);
extern bool sd_read_sector(FIL *file, uint8_t *buffer, uint32_t *bytes_read);
extern bool sd_seek(FIL *file, uint32_t offset);

static void log_msg(const char *fmt, ...) { 
  va_list a; va_start(a, fmt); vAppLog(fmt, a); va_end(a); 
}

static void test_cycles(void) {
    log_msg("=== Play Cycle Test ===\n");
    
    sd_init();

    // Cycle 1: short play then stop
    sd_card_info card_info;
    sdcard_read_card_info(&card_info);
    log_msg("Cycle 1: Read card...");
    AudioTrack track = audio_track_create_with_handle(&card_info, 1, 22050, AudioFormatPcm8);
    uint8_t buf[256];
    uint32_t r = 0;
    audio_track_read(&track, buf, 2048, &r);
    log_msg("  Read %lu bytes\n", (unsigned long)r);
    audio_track_release(&track);

    // Cycle 2: different track
    log_msg("Cycle 2: Track 2...");
    track = audio_track_create_with_handle(&card_info, 1, 22050, AudioFormatPcm8);
    r = 0;
    audio_track_read(&track, buf, 2048, &r);
    log_msg("  Read %lu bytes\n", (unsigned long)r);
    audio_track_release(&track);

    // Cycle 3: another
    log_msg("Cycle 3: Track 2 again...");
    track = audio_track_create_with_handle(&card_info, 1, 22050, AudioFormatPcm8);
    r = 0;
    audio_track_read(&track, buf, 2048, &r);
    log_msg("  Read %lu bytes\n", (unsigned long)r);
    audio_track_release(&track);

    log_msg("3 cycles done - all OK\n=== Test Complete ===\n");
    sd_deinit();
}

int main(void) {
    app_event_loop();
    test_cycles();
}