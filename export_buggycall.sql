-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: buggycalldb
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` (`version_num`) VALUES ('003'),('4dbc5ff1187a'),('74c532f38763'),('perf_composite_idx_001');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `audit_trail`
--

LOCK TABLES `audit_trail` WRITE;
/*!40000 ALTER TABLE `audit_trail` DISABLE KEYS */;
INSERT INTO `audit_trail` (`id`, `hotel_id`, `user_id`, `action`, `entity_type`, `entity_id`, `old_values`, `new_values`, `ip_address`, `user_agent`, `created_at`) VALUES (1,1,14,'logout','user',14,NULL,NULL,NULL,NULL,'2025-11-16 18:15:22'),(2,1,2,'login_success','user',2,NULL,NULL,'127.0.0.1',NULL,'2025-11-16 18:15:26'),(3,1,8,'fcm_notification_sent','request',202,NULL,'{\"notification_type\": \"new_request\", \"priority\": \"high\", \"recipient_count\": 1, \"failed_count\": 0, \"driver_ids\": [10], \"driver_details\": [{\"id\": 10, \"name\": \"\\u00d6zlem K\\u00d6K\", \"buggy\": \"SHUTTLE-06\"}]}','127.0.0.1',NULL,'2025-11-16 18:38:27'),(4,1,10,'request_completed','request',202,NULL,'{\"completed_at\": \"2025-11-16T18:38:41\"}','127.0.0.1',NULL,'2025-11-16 18:38:41'),(5,1,2,'excel_report_exported','report',NULL,NULL,'{\"date_range\": \"week\", \"total_requests\": 2, \"filename\": \"shuttle_call_rapor_20251116_200238.xlsx\"}','127.0.0.1',NULL,'2025-11-16 19:02:38'),(6,1,10,'driver_disconnected','buggy',3,NULL,'{\"reason\": \"connection_lost\", \"buggy_code\": \"SHUTTLE-06\", \"driver_name\": \"ozlem\", \"status\": \"offline\"}',NULL,NULL,'2025-11-16 19:04:21'),(7,1,10,'driver_initial_location_set','buggy',3,NULL,'{\"location_id\": 2, \"location_name\": \"Merit Royal Diamond\"}','127.0.0.1',NULL,'2025-11-16 19:04:26'),(8,1,8,'fcm_notification_sent','request',203,NULL,'{\"notification_type\": \"new_request\", \"priority\": \"high\", \"recipient_count\": 1, \"failed_count\": 0, \"driver_ids\": [10], \"driver_details\": [{\"id\": 10, \"name\": \"\\u00d6zlem K\\u00d6K\", \"buggy\": \"SHUTTLE-06\"}]}','127.0.0.1',NULL,'2025-11-16 19:04:38'),(9,1,10,'request_completed','request',203,NULL,'{\"completed_at\": \"2025-11-16T19:04:50\"}','127.0.0.1',NULL,'2025-11-16 19:04:50'),(10,1,2,'pdf_report_exported','report',NULL,NULL,'{\"date_range\": \"week\", \"total_requests\": 3, \"filename\": \"shuttle_call_rapor_20251116_201206.pdf\", \"includes_charts\": true}','127.0.0.1',NULL,'2025-11-16 19:12:06'),(11,1,14,'login_success','user',14,NULL,NULL,'127.0.0.1',NULL,'2025-11-16 19:13:44'),(12,1,14,'driver_initial_location_set','buggy',7,NULL,'{\"location_id\": 3, \"location_name\": \"Merit Royal\"}','127.0.0.1',NULL,'2025-11-16 19:13:48'),(13,1,8,'fcm_notification_sent','request',204,NULL,'{\"notification_type\": \"new_request\", \"priority\": \"high\", \"recipient_count\": 1, \"failed_count\": 0, \"driver_ids\": [14], \"driver_details\": [{\"id\": 14, \"name\": \"Ayla KAYA\", \"buggy\": \"SHUTTLE-10\"}]}','127.0.0.1',NULL,'2025-11-16 19:14:05'),(14,1,14,'request_completed','request',204,NULL,'{\"completed_at\": \"2025-11-16T19:14:21\"}','127.0.0.1',NULL,'2025-11-16 19:14:21'),(15,1,14,'driver_disconnected','buggy',7,NULL,'{\"reason\": \"connection_lost\", \"buggy_code\": \"SHUTTLE-10\", \"driver_name\": \"ayla\", \"status\": \"offline\"}',NULL,NULL,'2025-11-16 19:15:25'),(16,1,14,'request_completed','request',205,NULL,'{\"completed_at\": \"2025-11-16T19:15:54\"}','127.0.0.1',NULL,'2025-11-16 19:15:54'),(17,1,2,'pdf_report_exported','report',NULL,NULL,'{\"date_range\": \"week\", \"total_requests\": 5, \"filename\": \"shuttle_call_rapor_20251116_201747.pdf\", \"includes_charts\": true}','127.0.0.1',NULL,'2025-11-16 19:17:47'),(18,1,2,'pdf_report_exported','report',NULL,NULL,'{\"date_range\": \"week\", \"total_requests\": 5, \"filename\": \"shuttle_call_rapor_20251116_203225.pdf\", \"includes_charts\": true}','127.0.0.1',NULL,'2025-11-16 19:32:25'),(19,1,2,'pdf_report_exported','report',NULL,NULL,'{\"date_range\": \"week\", \"total_requests\": 5, \"filename\": \"shuttle_call_rapor_20251116_203535.pdf\", \"includes_charts\": true}','127.0.0.1',NULL,'2025-11-16 19:35:35'),(20,1,2,'pdf_report_exported','report',NULL,NULL,'{\"date_range\": \"week\", \"total_requests\": 5, \"filename\": \"shuttle_call_rapor_20251116_204201.pdf\", \"includes_charts\": true}','127.0.0.1',NULL,'2025-11-16 19:42:01'),(21,1,2,'pdf_report_exported','report',NULL,NULL,'{\"date_range\": \"week\", \"total_requests\": 5, \"filename\": \"shuttle_call_rapor_20251116_204332.pdf\", \"includes_charts\": true}','127.0.0.1',NULL,'2025-11-16 19:43:32'),(22,1,14,'request_completed','request',206,NULL,'{\"completed_at\": \"2025-11-16T19:47:54\"}','127.0.0.1',NULL,'2025-11-16 19:47:54'),(23,1,14,'login_success','user',14,NULL,NULL,'127.0.0.1',NULL,'2025-11-17 12:58:22'),(24,1,14,'driver_initial_location_set','buggy',7,NULL,'{\"location_id\": 2, \"location_name\": \"Merit Royal Diamond\"}','127.0.0.1',NULL,'2025-11-17 12:58:25'),(25,1,14,'request_completed','request',207,NULL,'{\"completed_at\": \"2025-11-17T12:58:42\"}','127.0.0.1',NULL,'2025-11-17 12:58:42');
/*!40000 ALTER TABLE `audit_trail` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `buggies`
--

LOCK TABLES `buggies` WRITE;
/*!40000 ALTER TABLE `buggies` DISABLE KEYS */;
INSERT INTO `buggies` (`id`, `hotel_id`, `current_location_id`, `driver_id`, `code`, `model`, `license_plate`, `icon`, `status`, `created_at`, `updated_at`) VALUES (1,1,NULL,NULL,'SHUTTLE-04','Golf Cart','SHUTTLE-04','🚐','OFFLINE','2025-11-13 18:01:41','2025-11-16 13:50:44'),(2,1,NULL,NULL,'SHUTTLE-05','Golf Cart','SHUTTLE-05','🚐','OFFLINE','2025-11-13 18:01:41','2025-11-13 18:01:41'),(3,1,4,NULL,'SHUTTLE-06','Golf Cart','SHUTTLE-06','🚐','BUSY','2025-11-13 18:01:41','2025-11-16 19:04:50'),(4,1,NULL,NULL,'SHUTTLE-07','Golf Cart','SHUTTLE-07','🚐','OFFLINE','2025-11-13 18:01:41','2025-11-13 18:01:41'),(5,1,NULL,NULL,'SHUTTLE-08','Golf Cart','SHUTTLE-08','🚐','OFFLINE','2025-11-13 18:01:41','2025-11-13 18:01:41'),(6,1,NULL,NULL,'SHUTTLE-09','Golf Cart','SHUTTLE-09','🚐','OFFLINE','2025-11-13 18:01:41','2025-11-13 18:01:41'),(7,1,3,NULL,'SHUTTLE-10','Golf Cart','SHUTTLE-10','🚐','AVAILABLE','2025-11-13 18:01:41','2025-11-17 12:58:42'),(8,1,NULL,NULL,'SHUTTLE-11','Golf Cart','SHUTTLE-11','🚐','OFFLINE','2025-11-13 18:01:41','2025-11-13 18:01:41'),(9,1,NULL,NULL,'SHUTTLE-12','Golf Cart','SHUTTLE-12','🚐','OFFLINE','2025-11-13 18:01:41','2025-11-13 18:01:41'),(10,1,NULL,NULL,'SHUTTLE-13','Golf Cart','SHUTTLE-13','🚐','OFFLINE','2025-11-13 18:01:41','2025-11-13 18:01:41');
/*!40000 ALTER TABLE `buggies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `buggy_drivers`
--

LOCK TABLES `buggy_drivers` WRITE;
/*!40000 ALTER TABLE `buggy_drivers` DISABLE KEYS */;
INSERT INTO `buggy_drivers` (`id`, `buggy_id`, `driver_id`, `is_active`, `is_primary`, `assigned_at`, `last_active_at`) VALUES (1,1,8,0,1,'2025-11-13 18:01:42','2025-11-16 10:51:44'),(2,2,9,0,1,'2025-11-13 18:01:42',NULL),(3,3,10,1,1,'2025-11-13 18:01:42','2025-11-16 19:04:26'),(4,4,11,0,1,'2025-11-13 18:01:42',NULL),(5,5,12,0,1,'2025-11-13 18:01:42',NULL),(6,6,13,0,1,'2025-11-13 18:01:42',NULL),(7,7,14,1,1,'2025-11-13 18:01:42','2025-11-17 10:58:22'),(8,8,15,0,1,'2025-11-13 18:01:42',NULL),(9,9,16,0,1,'2025-11-13 18:01:42',NULL),(10,10,17,0,1,'2025-11-13 18:01:42',NULL);
/*!40000 ALTER TABLE `buggy_drivers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `buggy_requests`
--

LOCK TABLES `buggy_requests` WRITE;
/*!40000 ALTER TABLE `buggy_requests` DISABLE KEYS */;
INSERT INTO `buggy_requests` (`id`, `hotel_id`, `location_id`, `completion_location_id`, `buggy_id`, `accepted_by_id`, `guest_name`, `room_number`, `has_room`, `phone`, `notes`, `status`, `cancelled_by`, `requested_at`, `accepted_at`, `completed_at`, `cancelled_at`, `timeout_at`, `response_time`, `completion_time`, `guest_push_subscription`, `guest_fcm_token`, `guest_fcm_token_expires_at`) VALUES (201,1,3,5,7,14,NULL,NULL,1,NULL,NULL,NULL,'COMPLETED',NULL,'2025-11-16 18:10:03','2025-11-16 18:10:09','2025-11-16 18:13:39',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(202,1,2,5,3,10,NULL,NULL,1,NULL,NULL,NULL,'COMPLETED',NULL,'2025-11-16 18:38:25','2025-11-16 18:40:36','2025-11-16 18:42:41',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(203,1,2,4,3,10,NULL,NULL,1,NULL,NULL,NULL,'COMPLETED',NULL,'2025-11-16 19:04:35','2025-11-16 19:04:45','2025-11-16 19:04:50',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(204,1,4,6,7,14,NULL,NULL,1,NULL,NULL,NULL,'COMPLETED',NULL,'2025-11-16 19:14:04','2025-11-16 19:14:09','2025-11-16 19:14:21',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(205,1,6,3,7,14,NULL,NULL,1,NULL,NULL,NULL,'COMPLETED',NULL,'2025-11-16 19:15:42','2025-11-16 19:15:45','2025-11-16 19:15:54',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(206,1,6,4,7,14,NULL,NULL,1,NULL,NULL,NULL,'COMPLETED',NULL,'2025-11-16 19:47:38','2025-11-16 19:47:44','2025-11-16 19:47:54',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(207,1,2,3,7,14,NULL,NULL,1,NULL,NULL,NULL,'COMPLETED',NULL,'2025-11-17 12:58:00','2025-11-17 12:58:30','2025-11-17 12:58:42',NULL,NULL,NULL,NULL,NULL,'dfPYCPRJXpn4i-TbaqRIXt:APA91bGoCIF03EI3GIa9xFD0wIG7VoTZ23zvaE8_rcHe-bRL_tcrmCPtxgB_IILkBiUgJmE4mQXYkSMBHxS8knNxSLWBD_OxNBpdSDEqTg3uE3wBxYXgBrw','2025-11-17 11:58:04');
/*!40000 ALTER TABLE `buggy_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `hotels`
--

LOCK TABLES `hotels` WRITE;
/*!40000 ALTER TABLE `hotels` DISABLE KEYS */;
INSERT INTO `hotels` (`id`, `name`, `code`, `address`, `phone`, `email`, `logo`, `timezone`, `created_at`, `updated_at`) VALUES (1,'Test Otel','TEST',NULL,NULL,NULL,NULL,'Europe/Istanbul','2025-11-04 15:15:17','2025-11-04 15:15:17');
/*!40000 ALTER TABLE `hotels` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `locations`
--

LOCK TABLES `locations` WRITE;
/*!40000 ALTER TABLE `locations` DISABLE KEYS */;
INSERT INTO `locations` (`id`, `hotel_id`, `name`, `description`, `qr_code_data`, `qr_code_image`, `display_order`, `latitude`, `longitude`, `is_active`, `created_at`, `updated_at`, `location_image`) VALUES (2,1,'Merit Royal Diamond','Merit Royal Diamond','http://192.168.1.100:5000/guest/call?l=2','data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADoAAAA6AQAAAADJwHeFAAAA30lEQVR4nFWRvWoDMRCE526vMQjkNr0h7cIWJnCwfnQFpQkonCGVwQ8hI5U6lCagvS0/Zmd/BqAknoEZ/zVrrmmnPghYSm+FBlmAJ16CA7ng7d0QaNHGxfhMIAb2u9H03n3UHgZZI7JLlrDmVOJmuohXEsBquveZgiGOY+5utbMcowQdmvl1+Q1P2m+mS0tfs/VJwq6hDbLUU61fev0ZGqFNekt2lqJQtN9gSmuEBHu75KZmw2Wibz/JKdgsbjW6g4/EtcEdCLus7ZDFdj+Xq8nUh7q3x8Nc8Xn+AFCH5g8ZiWVfnJkqgwAAAABJRU5ErkJggg==',1,NULL,NULL,1,'2025-11-04 16:22:11','2025-11-16 14:43:30','/static/uploads/locations/a0d8903941f7498cad800f7ef79debcf.png'),(3,1,'Merit Royal','Merit Royal','http://192.168.1.100:5000/guest/call?l=3','data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADoAAAA6AQAAAADJwHeFAAAA6UlEQVR4nFWRsWpEIRBF7z5tFgaykCr9wraCWwo+yCdtm89KG3AxpUE/IJBfcFF4jeJWwXlTXu49c3UA4XRUwIL/sSUO0mMqy2PtyE4yBdjSN1hKAji/XfYc0VRhnAOEAnpiqYHHX/0Y95kynhSF4aYSLVHxkXGUQFI/mJ4lEsKXcGy7U1ENMkzRlF1xlqX65X39FX2d5HGqpn8mztEUGhrr42OEs5r1MdtxCz1dpye/DC08/w0DYTw044wB1SxruByki7Lyd9l8u3riHKVza6DdLV5TtXnniRZF72/aWqBJlvfT8Uyo0/MEdEdjxMdw8jwAAAAASUVORK5CYII=',2,NULL,NULL,1,'2025-11-04 16:34:56','2025-11-16 14:43:38','/static/uploads/locations/b872224290f643c89a8e69249cc479e8.png'),(4,1,'Merit Royal Premium','Merit Royal Premium','http://192.168.1.100:5000/guest/call?l=4','data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADoAAAA6AQAAAADJwHeFAAAA5ElEQVR4nFWQMWoDMRBF/+64WRBMnSpXEKhwszAX8D1yER/JB5BRq0UBHyKtghbcaJk0JhqrfPx5M18Aubh6YMbrneSGC0infwIfHDTQyMzAz7pHOwVs+3K2hG8fzzP68EwgDxzfJqO4uy/W+9gVamde28gguaqxdkMcSUxi7gGX6lvTOEghoixsMqF3Il2tJ7Fm2wvEyXFqwzOFwz2OEM1vpO4lFWenKCMXNaRK8a3T8Myf19/HdlpMRlWovF0Icr0GMUSauijGAx8yF9iMD10A033y5LYnlv3Nw0Ul2l0smUz3PzR7W37nZbBoAAAAAElFTkSuQmCC',3,NULL,NULL,1,'2025-11-04 16:36:01','2025-11-16 14:43:54','/static/uploads/locations/1dbb3143ed64443abcbeed0f7e60b325.png'),(5,1,'Merit Royal Crystal','Merit Royal Crystal','http://192.168.1.100:5000/guest/call?l=5','data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADoAAAA6AQAAAADJwHeFAAAA3UlEQVR4nFWRQWoDMQxFf6JsAi4u9CIq7tLggawCOVwP0wO4qMsB5wC9QsDBgW5slFUZ2cuH/+NLAiiJY2CP/5dal9DUEA6t10Yb2QMvpzdgIv5xXGYPa7SeHYiBcTUp7eP302s2KfarwhtP9quUqaFQjavahqKt0doNQeMc4YyZtCeXsp1LVGSatBVXtFfT8HwPYxyM54AL/V39Y9lSlbWLN/tBV99IbGcwg6e5VF3KKdg/BGiwe05Vy7sbhtyX3fDf0fZB+XD5BEswBt1eN+K/jpHGZbrFYIefzfMEyI5hSO1FDicAAAAASUVORK5CYII=',4,NULL,NULL,1,'2025-11-04 16:36:52','2025-11-16 14:44:05','/static/uploads/locations/6b0f171c1e594e9f875ddcce483e70cd.png'),(6,1,'Merit International Casino','Merit International Casino','http://192.168.1.100:5000/guest/call?l=6','data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADoAAAA6AQAAAADJwHeFAAAA30lEQVR4nFWRQWoDMQxFf0bdFAwKdNtDuLhLg3OAHi6HyQEELnQzJXOAXqHg4MBQsFFXwbKXj6/HtwQQ8uqBBY+XakaoaogPJZZKgyzAK70AE6H782n2eI3WcwB5oG9mSht+zqwyMunmtnrg2/BkZrpODSu5tqptmPkaaG2W1IAIN8xQDeqSmAwTKE8/Fc2srUyZtja04Vl63PeN7ydjltoym/2gxVIp284ELx4M24dUUjAEFEWD3XMqF35zfbqFdwlR7ObzvsnXyDwB339H+j0Owhe8h/4x3aJH4HN4/gHlUV997zGU2gAAAABJRU5ErkJggg==',5,NULL,NULL,1,'2025-11-04 18:31:29','2025-11-16 14:44:17','/static/uploads/locations/0e1b87fb5d3841ad91e7c02129fc6bcc.png');
/*!40000 ALTER TABLE `locations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `notification_logs`
--

LOCK TABLES `notification_logs` WRITE;
/*!40000 ALTER TABLE `notification_logs` DISABLE KEYS */;
INSERT INTO `notification_logs` (`id`, `user_id`, `notification_type`, `priority`, `title`, `body`, `status`, `error_message`, `retry_count`, `sent_at`, `delivered_at`, `clicked_at`) VALUES (2,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 07:36:11',NULL,NULL),(3,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 07:36:15',NULL,NULL),(4,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 13:24:11',NULL,NULL),(5,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 13:24:19',NULL,NULL),(6,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 13:50:05',NULL,NULL),(7,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 13:50:13',NULL,NULL),(8,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 13:58:22',NULL,NULL),(9,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 14:15:53',NULL,NULL),(10,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 14:16:08',NULL,NULL),(11,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 14:32:33',NULL,NULL),(12,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 14:32:38',NULL,NULL),(13,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 14:41:41',NULL,NULL),(14,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 14:41:47',NULL,NULL),(15,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 14:47:00',NULL,NULL),(16,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 14:47:21',NULL,NULL),(17,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 14:54:38',NULL,NULL),(18,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 14:54:50',NULL,NULL),(19,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 15:04:23',NULL,NULL),(20,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 15:04:29',NULL,NULL),(21,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 15:10:26',NULL,NULL),(22,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 15:10:31',NULL,NULL),(23,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 15:10:34',NULL,NULL),(24,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 15:10:40',NULL,NULL),(25,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 15:11:57',NULL,NULL),(26,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 15:12:05',NULL,NULL),(27,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 17:28:11',NULL,NULL),(28,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 17:28:47',NULL,NULL),(29,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 17:32:37',NULL,NULL),(30,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 17:43:33',NULL,NULL),(31,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 17:48:25',NULL,NULL),(32,8,'fcm','normal','✅ Shuttle Ulaştı!','Shuttle\'ınız hedefe ulaştı. İyi yolculuklar!','sent',NULL,0,'2025-11-16 17:48:44',NULL,NULL),(33,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 18:10:09',NULL,NULL),(34,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-06','sent',NULL,0,'2025-11-16 18:38:36',NULL,NULL),(35,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-06','sent',NULL,0,'2025-11-16 19:04:45',NULL,NULL),(36,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 19:14:09',NULL,NULL),(37,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 19:15:47',NULL,NULL),(38,8,'fcm','high','🎉 Shuttle Kabul Edildi!','Shuttle size doğru geliyor. Buggy: SHUTTLE-10','sent',NULL,0,'2025-11-16 19:47:46',NULL,NULL);
/*!40000 ALTER TABLE `notification_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `sessions`
--

LOCK TABLES `sessions` WRITE;
/*!40000 ALTER TABLE `sessions` DISABLE KEYS */;
/*!40000 ALTER TABLE `sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `system_users`
--

LOCK TABLES `system_users` WRITE;
/*!40000 ALTER TABLE `system_users` DISABLE KEYS */;
INSERT INTO `system_users` (`id`, `hotel_id`, `username`, `password_hash`, `role`, `full_name`, `email`, `phone`, `is_active`, `must_change_password`, `fcm_token`, `fcm_token_date`, `push_subscription`, `push_subscription_date`, `notification_preferences`, `created_at`, `last_login`) VALUES (2,1,'superadmin','scrypt:32768:8:1$RfAEXyxrYhpPBfUf$8ed76d38a98506900502e8bcd4a652ac4df3d016202898a936b38e6d134b7a5710b498218a5787ff5d93d9d9212b6b46a27cfbc7c7e2ad3bb3eae4d76600d4b8','ADMIN','Super Admin','superadmin@test.com',NULL,1,0,NULL,NULL,NULL,NULL,NULL,'2025-11-04 15:15:17','2025-11-16 16:15:26'),(8,1,'hasan','scrypt:32768:8:1$b6mrZpZniDOqwhEQ$fb7becc590511026a23236642bb7e2e4486a1157bd8e50b322d59c57f5c892826f7796b81e0786dac5d194ee0321064165ad61801f0909dfca05fa028885662b','DRIVER','Hasan MİRİOĞLU',NULL,NULL,1,0,'fmzIhu3z1dkJg7a_77HVeM:APA91bHn-W9u6GxjI4AmhkATX6mCm_fY9IO-E3hBWmCzoE3OIz9AvLjRUxYG92g0nPujcLBcDt3ov6Hm5iqIKAHnJbKCygjmVvlvF94COWf8dGBZoGkdEDU','2025-11-16 10:51:48',NULL,NULL,NULL,'2025-11-13 18:01:41','2025-11-16 10:49:33'),(9,1,'mehmet','scrypt:32768:8:1$cMZXLIwasqKvaetd$4e8fd0779547a5ebed65501c5654cdb6647591393d49ad72a9dee5945e54c5c3e5aea3e0d726ce3586592433866c987736690c2067e45afc94493b466bba869a','DRIVER','Mehmet KARAKURT',NULL,NULL,1,0,NULL,NULL,NULL,NULL,NULL,'2025-11-13 18:01:41',NULL),(10,1,'ozlem','scrypt:32768:8:1$rcXsnhkPgkUDovQW$83a98080e58235a2c57db61c180426803efb156b5fbb756fe6d194c941357015b86b40d12cf8bffe1a57f979ba5ae5ab7b22b1b28936fba2f2d960750c3212f7','DRIVER','Özlem KÖK',NULL,NULL,1,0,'eN3zcNocbcWNsC_zzk12RF:APA91bEGCKbrckcP9nkECVpw5-lTzZLCUD6OJiIbuw5g_mnqmWuLuvYqZ5vDhiMyEklTDjQp2Hki2CcrT_4bl2RCdYpeFQG25Oh7mR0CtrrCSf8TzSl6I9Q','2025-11-16 19:04:50',NULL,NULL,NULL,'2025-11-13 18:01:41','2025-11-16 10:53:59'),(11,1,'mustafao','scrypt:32768:8:1$B0WU90KaoOQQxdNF$18e17cdd94d2e1ce744faa78d79c94564add035e594445e1a3f01f06419538cb0e5cc0cde2ffe6ce31b3cad817f194343e1de573a832147c379d6abf5575c473','DRIVER','Mustafa ÖZÇELİK',NULL,NULL,1,0,NULL,NULL,NULL,NULL,NULL,'2025-11-13 18:01:41',NULL),(12,1,'mohammad','scrypt:32768:8:1$3kBlAnswA2o5lkEC$aa39d83a0a3f0b3afe492cb59641ee8b2ebaf3718d33f4af62804c5645bd9f3860213fb9558586c4b043cd2d20b3c41ba4cd32f444734dc0913ffa88619e6d71','DRIVER','Mohammad Sadra SEPANJI',NULL,NULL,1,0,NULL,NULL,NULL,NULL,NULL,'2025-11-13 18:01:41',NULL),(13,1,'ferhan','scrypt:32768:8:1$HYLrsl5k3Hg7QGUJ$56b103c8b5f02140332c3a7525c50dbda488fcb72faba06d6e714b897632ac77205c1e48c41b0171d680dd8fe77d0ae1a27b475ff43d6fdbd87b2a0ba956c387','DRIVER','Ferhan ZENGİN',NULL,NULL,1,0,NULL,NULL,NULL,NULL,NULL,'2025-11-13 18:01:41',NULL),(14,1,'ayla','scrypt:32768:8:1$BWV1aekMRLG0V141$572b03146e29ee7e4c5ee8311b6b0db90ab98dfff41e68930b816111a0da3ae3888bbaa373a64726042ff58c1fad768d9c9a750f7ec6484a3a6445c80b74a418','DRIVER','Ayla KAYA',NULL,NULL,1,0,'erjs1jdBR7Q9hViDQcGAm6:APA91bEbibZlq4VY0KEx_Vv-WWTZK5u2gw3Lhye0R5kBJMNB8y_rRA5UFQ7zPe9OXR8dJBYVgKG3SFFjy5Konu_H6hYbi4Fs_ROpwKfNtmrIBRFjN8of8Vw','2025-11-17 12:58:42',NULL,NULL,NULL,'2025-11-13 18:01:41','2025-11-17 10:58:22'),(15,1,'mustafab','scrypt:32768:8:1$6vdXoyHF5IyCVEKk$a65a9e05bc8ce5d7fdea42d3453f8a0c5366b95fb242fa37d2f7097c53cc8dc3fcb755b08105b931577c01393228af9ad71e71626ef9be9ce76f6a5a58623ca5','DRIVER','Mustafa BERAZİ',NULL,NULL,1,0,NULL,NULL,NULL,NULL,NULL,'2025-11-13 18:01:41',NULL),(16,1,'fatma','scrypt:32768:8:1$aWHeAj1jDitAao71$fc4016192e541b4b231bd7a6109deb848f111c64037428f776b1d3d198dc790842e818adbdd8c0903c5d017b364479ad156edcb2baa1d19fdb842c753c2fa7bb','DRIVER','Fatma ALTUNTAŞ',NULL,NULL,1,0,NULL,NULL,NULL,NULL,NULL,'2025-11-13 18:01:41',NULL),(17,1,'ahmet','scrypt:32768:8:1$G5v8pPNgxfMjsmgQ$af7e933b411045de7aa2755cb6b83603e20e25c6db88c5a13ba9963bc893a6c023bff4b9e8795afd23769a15f27f85f5a0ebc8325f266438ba9facc5d34f1a13','DRIVER','Ahmet CİĞERLİ',NULL,NULL,1,0,NULL,NULL,NULL,NULL,NULL,'2025-11-13 18:01:41',NULL);
/*!40000 ALTER TABLE `system_users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-10 13:11:13
