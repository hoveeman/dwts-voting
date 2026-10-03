//
//  BallroomWidgetsLiveActivity.swift
//  BallroomWidgets
//
//  Created by Trent Hoverman on 10/3/26.
//

import ActivityKit
import WidgetKit
import SwiftUI

public struct BallroomWidgetsLiveActivity: Widget {
    public init() {}

    public var body: some WidgetConfiguration {
        ActivityConfiguration(for: DWTSLiveActivityAttributes.self) { context in
            // Lock Screen / StandBy Banner
            LockScreenLiveActivityView(state: context.state)
                .activityBackgroundTint(Color(red: 0.10, green: 0.10, blue: 0.12))
                .activitySystemActionForegroundColor(Color(red: 0.95, green: 0.77, blue: 0.25)) // Gold
        } dynamicIsland: { context in
            DynamicIsland {
                // Expanded View (Long Press)
                DynamicIslandExpandedRegion(.leading) {
                    HStack(spacing: 6) {
                        Text("🪩")
                            .font(.system(size: 20))
                        VStack(alignment: .leading, spacing: 2) {
                            Text(context.state.coupleName)
                                .font(.system(size: 14, weight: .bold))
                                .foregroundColor(.white)
                                .lineLimit(1)
                            Text(context.state.danceStyle)
                                .font(.system(size: 12))
                                .foregroundColor(Color(white: 0.7))
                        }
                    }
                    .padding(.leading, 4)
                }

                DynamicIslandExpandedRegion(.trailing) {
                    VStack(alignment: .trailing, spacing: 2) {
                        HStack(spacing: 2) {
                            Text("\(context.state.score)")
                                .font(.system(size: 18, weight: .black))
                                .foregroundColor(Color(red: 0.95, green: 0.77, blue: 0.25))
                            Text("/\(context.state.maxScore)")
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundColor(Color(white: 0.6))
                        }
                        if !context.state.judgeBreakdown.isEmpty {
                            Text(context.state.judgeBreakdown)
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(Color(white: 0.8))
                        }
                    }
                    .padding(.trailing, 4)
                }

                DynamicIslandExpandedRegion(.bottom) {
                    VStack(spacing: 6) {
                        Divider().background(Color(white: 0.25))
                        HStack {
                            Text("📊 \(context.state.dancedCount)/\(context.state.totalCouples) danced")
                                .font(.system(size: 11, weight: .medium))
                                .foregroundColor(Color(white: 0.8))

                            Spacer()

                            if let next = context.state.nextCoupleName {
                                Text("⏳ Next: \(next)")
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundColor(Color(red: 0.95, green: 0.77, blue: 0.25))
                                    .lineLimit(1)
                            }
                        }
                        
                        // SMS Vote Deep Link Action
                        Link(destination: URL(string: "sms:21523")!) {
                            HStack {
                                Text("📱 Tap to Cast 10 SMS Votes (21523)")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundColor(.black)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 5)
                            .background(Color(red: 0.95, green: 0.77, blue: 0.25))
                            .cornerRadius(6)
                        }
                    }
                    .padding(.horizontal, 4)
                }
            } compactLeading: {
                // Compact Leading: Mirrorball + Leader/Rank
                HStack(spacing: 3) {
                    Text("🪩")
                        .font(.system(size: 12))
                    Text("#\(context.state.leaderboardRank)")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(Color(red: 0.95, green: 0.77, blue: 0.25))
                }
            } compactTrailing: {
                // Compact Trailing: Latest Score (e.g. 26/30)
                HStack(spacing: 1) {
                    Text("\(context.state.score)")
                        .font(.system(size: 12, weight: .black))
                        .foregroundColor(.white)
                    Text("/\(context.state.maxScore)")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(Color(white: 0.6))
                }
            } minimal: {
                // Minimal (Shared Island): Tiny score
                Text("\(context.state.score)")
                    .font(.system(size: 11, weight: .black))
                    .foregroundColor(Color(red: 0.95, green: 0.77, blue: 0.25))
            }
        }
    }
}

// Lock Screen / StandBy Banner View
struct LockScreenLiveActivityView: View {
    let state: DWTSLiveActivityAttributes.ContentState

    var body: some View {
        VStack(spacing: 10) {
            // Header: Show theme + Live pill
            HStack {
                HStack(spacing: 5) {
                    Text("🪩")
                    Text("Week \(state.weekNumber) · \(state.weekTheme)")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(Color(red: 0.95, green: 0.77, blue: 0.25))
                }
                Spacer()
                HStack(spacing: 4) {
                    Circle()
                        .fill(Color.red)
                        .frame(width: 6, height: 6)
                    Text("LIVE")
                        .font(.system(size: 10, weight: .black))
                        .foregroundColor(.red)
                }
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.red.opacity(0.15))
                .cornerRadius(4)
            }

            // Routine Scored Card
            HStack(alignment: .center) {
                VStack(alignment: .leading, spacing: 3) {
                    Text(state.coupleName)
                        .font(.system(size: 16, weight: .heavy))
                        .foregroundColor(.white)
                    
                    HStack(spacing: 4) {
                        Text(state.danceStyle)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(Color(white: 0.9))
                        if !state.songTitle.isEmpty {
                            Text("· \(state.songTitle)")
                                .font(.system(size: 11))
                                .foregroundColor(Color(white: 0.65))
                                .lineLimit(1)
                        }
                    }
                }

                Spacer()

                // Score Badge
                VStack(alignment: .trailing, spacing: 2) {
                    HStack(alignment: .firstTextBaseline, spacing: 2) {
                        Text("\(state.score)")
                            .font(.system(size: 26, weight: .black))
                            .foregroundColor(Color(red: 0.95, green: 0.77, blue: 0.25))
                        Text("/\(state.maxScore)")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundColor(Color(white: 0.6))
                    }
                    if !state.judgeBreakdown.isEmpty {
                        Text(state.judgeBreakdown)
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(Color(white: 0.8))
                    }
                }
            }
            .padding(10)
            .background(Color(white: 0.14))
            .cornerRadius(10)

            // Progress & Footer Info
            HStack {
                Text("📊 \(state.dancedCount) of \(state.totalCouples) danced")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(Color(white: 0.7))

                Spacer()

                if let elim = state.eliminationText {
                    Text("⚠️ \(elim)")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(Color.red)
                } else if let next = state.nextCoupleName {
                    Text("⏳ Next: \(next)")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(Color(red: 0.95, green: 0.77, blue: 0.25))
                }
            }
        }
        .padding(14)
        .background(Color(red: 0.08, green: 0.09, blue: 0.10))
    }
}
