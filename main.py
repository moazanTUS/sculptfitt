import tkinter as tk
from tkinter import filedialog

from backend.analyzers.squat_analyzer import SquatAnalyzer
from backend.analyzers.pushup_analyzer import PushupAnalyzer
from backend.analyzers.shoulder_press_analyzer import ShoulderPressAnalyzer
from backend.analyzers.user_image_analyzer import UserImageAnalyzer


def choose_exercise():
    print("\n🏋️ Welcome to SculpFit AI Analyzer 🧠")
    print("What do you want to analyze?\n")
    print("1. Squats")
    print("2. Pushups")
    print("3. Shoulder Press")
    print("4. Lunges (coming soon)")
    print("5. Personal Image (Gemini)")
    print("0. Exit")

    choice = input("\nEnter your choice (0–5): ")

    if choice == "1":
        return "squats"
    elif choice == "2":
        return "pushups"
    elif choice == "3":
        return "shoulder_press"
    elif choice == "4":
        print("⚠️ Lunge analyzer not implemented yet.")
        return None
    elif choice == "5":
        return "user_image"
    elif choice == "0":
        print("👋 Exiting...")
        exit(0)
    else:
        print("❌ Invalid choice. Please enter 0–5.")
        return None


def select_video_file():
    # ✅ Create and destroy a fresh root every time (most reliable on Windows)
    root = tk.Tk()
    root.withdraw()
    root.lift()
    root.attributes("-topmost", True)

    video_file = filedialog.askopenfilename(
        title="Select a video file",
        filetypes=[("Video Files", "*.mp4 *.mov *.avi")],
    )

    root.destroy()
    return video_file


def select_image_file():
    root = tk.Tk()
    root.withdraw()
    root.lift()
    root.attributes("-topmost", True)

    image_file = filedialog.askopenfilename(
        title="Select an image file",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp *.heic *.heif")],
    )

    root.destroy()
    return image_file


def run_exercise_video_analysis(exercise: str):
    print("\n📂 Select a video file for analysis...")
    video_file = select_video_file()

    if not video_file:
        print("❌ No file selected. Returning to menu...")
        return

    if exercise == "squats":
        analyzer = SquatAnalyzer(video_file)
    elif exercise == "pushups":
        analyzer = PushupAnalyzer(video_file)
    elif exercise == "shoulder_press":
        analyzer = ShoulderPressAnalyzer(video_file)
    else:
        print("🚧 Analyzer for this exercise not available yet.")
        return

    report = analyzer.analyze()

    print("\n✅ Analysis complete!")
    print("--------------------------------------------------")
    print(f"Exercise: {report['exercise']}")
    print(f"Total Reps: {report['total_reps']}")
    print(f"Perfect Reps: {report['perfect_reps']}")
    print(f"Partial Reps: {report['partial_reps']}")
    print(f"Form Score: {report['form_score']}%")
    print("--------------------------------------------------")
    print(f"Annotated video saved at: {report['annotated_video']}")
    print("--------------------------------------------------\n")


def run_user_image_analysis():
    print("\n🖼️ Select an image file for Gemini analysis...")
    image_file = select_image_file()

    if not image_file:
        print("❌ No image selected. Returning to menu...")
        return

    analyzer = UserImageAnalyzer(
        image_path=image_file,
         api_key="AIzaSyB-Bc1V1S1OCxLu7rtvq5WkT_cOA1gCzD4",  # optional hardcode
    )

    try:
        report = analyzer.analyze()
    except Exception as e:
        print(f"\n❌ Gemini image analysis failed: {e}\n")
        return

    data = report["result"]
    print("\n✅ Image analysis complete (JSON)!")
    print("--------------------------------------------------")
    print(f"Body Type: {data.get('body_type')}")
    print(f"Focus Areas: {data.get('focus_areas')}")
    print("--------------------------------------------------\n")


def main():
    while True:
        choice = choose_exercise()
        if not choice:
            continue

        if choice == "user_image":
            run_user_image_analysis()
        else:
            run_exercise_video_analysis(choice)

        again = input("Would you like to analyze another file? (y/n): ").lower()
        if again != "y":
            print("\n👋 Thanks for using SculpFit AI Analyzer!")
            break


if __name__ == "__main__":
    main()
