package com.quantum.batch.controller;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.quartz.JobDetail;
import org.quartz.JobKey;
import org.quartz.Scheduler;
import org.quartz.SchedulerException;
import org.quartz.Trigger;
import org.quartz.TriggerKey;
import org.quartz.impl.matchers.GroupMatcher;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/** Quartz 스케줄러 관리 API Job과 Trigger의 동적 관리 기능 제공 */
@Slf4j
@RestController
@RequestMapping("/api/quartz")
@RequiredArgsConstructor
public class QuartzController {

    private final Scheduler scheduler;

    /** 모든 Job 목록 조회 */
    @GetMapping("/jobs")
    public ResponseEntity<Map<String, Object>> getAllJobs() {
        try {
            Set<JobKey> jobKeys = scheduler.getJobKeys(GroupMatcher.anyGroup());

            List<Map<String, Object>> jobs =
                    jobKeys.stream().map(this::getJobInfo).collect(Collectors.toList());

            Map<String, Object> response = new HashMap<>();
            response.put("totalJobs", jobs.size());
            response.put("jobs", jobs);
            response.put("schedulerName", scheduler.getSchedulerName());
            response.put("schedulerInstanceId", scheduler.getSchedulerInstanceId());

            return ResponseEntity.ok(response);

        } catch (SchedulerException e) {
            log.error("Failed to get jobs: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError()
                    .body(Map.of("error", "Failed to get jobs: " + e.getMessage()));
        }
    }

    /** 특정 Job의 상세 정보 조회 */
    @GetMapping("/jobs/{group}/{name}")
    public ResponseEntity<Map<String, Object>> getJobDetail(
            @PathVariable String group, @PathVariable String name) {
        try {
            JobKey jobKey = JobKey.jobKey(name, group);
            JobDetail jobDetail = scheduler.getJobDetail(jobKey);

            if (jobDetail == null) {
                return ResponseEntity.notFound().build();
            }

            Map<String, Object> jobInfo = getJobInfo(jobKey);

            // Trigger 정보 추가
            List<? extends Trigger> triggers = scheduler.getTriggersOfJob(jobKey);
            List<Map<String, Object>> triggerInfos =
                    triggers.stream().map(this::getTriggerInfo).collect(Collectors.toList());

            jobInfo.put("triggers", triggerInfos);

            return ResponseEntity.ok(jobInfo);

        } catch (SchedulerException e) {
            log.error("Failed to get job detail: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError()
                    .body(Map.of("error", "Failed to get job detail: " + e.getMessage()));
        }
    }

    /** Job 즉시 실행 */
    @PostMapping("/jobs/{group}/{name}/trigger")
    public ResponseEntity<Map<String, Object>> triggerJob(
            @PathVariable String group, @PathVariable String name) {
        try {
            JobKey jobKey = JobKey.jobKey(name, group);

            if (!scheduler.checkExists(jobKey)) {
                return ResponseEntity.notFound().build();
            }

            scheduler.triggerJob(jobKey);

            log.info("Job triggered manually: {}", jobKey);

            return ResponseEntity.ok(
                    Map.of("message", "Job triggered successfully", "jobKey", jobKey.toString()));

        } catch (SchedulerException e) {
            log.error("Failed to trigger job: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError()
                    .body(Map.of("error", "Failed to trigger job: " + e.getMessage()));
        }
    }

    /** Trigger 일시 정지 */
    @PostMapping("/triggers/{group}/{name}/pause")
    public ResponseEntity<Map<String, Object>> pauseTrigger(
            @PathVariable String group, @PathVariable String name) {
        try {
            TriggerKey triggerKey = TriggerKey.triggerKey(name, group);

            if (!scheduler.checkExists(triggerKey)) {
                return ResponseEntity.notFound().build();
            }

            scheduler.pauseTrigger(triggerKey);

            log.info("Trigger paused: {}", triggerKey);

            return ResponseEntity.ok(
                    Map.of(
                            "message",
                            "Trigger paused successfully",
                            "triggerKey",
                            triggerKey.toString()));

        } catch (SchedulerException e) {
            log.error("Failed to pause trigger: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError()
                    .body(Map.of("error", "Failed to pause trigger: " + e.getMessage()));
        }
    }

    /** Trigger 재시작 */
    @PostMapping("/triggers/{group}/{name}/resume")
    public ResponseEntity<Map<String, Object>> resumeTrigger(
            @PathVariable String group, @PathVariable String name) {
        try {
            TriggerKey triggerKey = TriggerKey.triggerKey(name, group);

            if (!scheduler.checkExists(triggerKey)) {
                return ResponseEntity.notFound().build();
            }

            scheduler.resumeTrigger(triggerKey);

            log.info("Trigger resumed: {}", triggerKey);

            return ResponseEntity.ok(
                    Map.of(
                            "message",
                            "Trigger resumed successfully",
                            "triggerKey",
                            triggerKey.toString()));

        } catch (SchedulerException e) {
            log.error("Failed to resume trigger: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError()
                    .body(Map.of("error", "Failed to resume trigger: " + e.getMessage()));
        }
    }

    /** 스케줄러 상태 조회 */
    @GetMapping("/scheduler/status")
    public ResponseEntity<Map<String, Object>> getSchedulerStatus() {
        try {
            Map<String, Object> status = new HashMap<>();
            status.put("schedulerName", scheduler.getSchedulerName());
            status.put("schedulerInstanceId", scheduler.getSchedulerInstanceId());
            status.put("isStarted", scheduler.isStarted());
            status.put("isInStandbyMode", scheduler.isInStandbyMode());
            status.put("isShutdown", scheduler.isShutdown());
            status.put("numJobsExecuted", scheduler.getMetaData().getNumberOfJobsExecuted());
            status.put("runningSince", scheduler.getMetaData().getRunningSince());

            return ResponseEntity.ok(status);

        } catch (SchedulerException e) {
            log.error("Failed to get scheduler status: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError()
                    .body(Map.of("error", "Failed to get scheduler status: " + e.getMessage()));
        }
    }

    /** Job 정보 추출 헬퍼 메서드 */
    private Map<String, Object> getJobInfo(JobKey jobKey) {
        try {
            JobDetail jobDetail = scheduler.getJobDetail(jobKey);
            Map<String, Object> jobInfo = new HashMap<>();

            jobInfo.put("key", jobKey.toString());
            jobInfo.put("name", jobKey.getName());
            jobInfo.put("group", jobKey.getGroup());
            jobInfo.put("description", jobDetail.getDescription());
            jobInfo.put("jobClass", jobDetail.getJobClass().getSimpleName());
            jobInfo.put("durable", jobDetail.isDurable());
            jobInfo.put("requestsRecovery", jobDetail.requestsRecovery());

            return jobInfo;

        } catch (SchedulerException e) {
            log.error("Failed to get job info for {}: {}", jobKey, e.getMessage());
            return Map.of("key", jobKey.toString(), "error", e.getMessage());
        }
    }

    /** Trigger 정보 추출 헬퍼 메서드 */
    private Map<String, Object> getTriggerInfo(Trigger trigger) {
        Map<String, Object> triggerInfo = new HashMap<>();

        triggerInfo.put("key", trigger.getKey().toString());
        triggerInfo.put("name", trigger.getKey().getName());
        triggerInfo.put("group", trigger.getKey().getGroup());
        triggerInfo.put("description", trigger.getDescription());
        triggerInfo.put("state", getTriggerState(trigger.getKey()));
        triggerInfo.put("nextFireTime", trigger.getNextFireTime());
        triggerInfo.put("previousFireTime", trigger.getPreviousFireTime());
        triggerInfo.put("startTime", trigger.getStartTime());
        triggerInfo.put("endTime", trigger.getEndTime());

        return triggerInfo;
    }

    /** Trigger 상태 조회 헬퍼 메서드 */
    private String getTriggerState(TriggerKey triggerKey) {
        try {
            return scheduler.getTriggerState(triggerKey).toString();
        } catch (SchedulerException e) {
            log.error("Failed to get trigger state for {}: {}", triggerKey, e.getMessage());
            return "UNKNOWN";
        }
    }
}
