use poise::serenity_prelude as serenity;
use serenity::{GatewayIntents, RoleId};
use std::fs::{File, OpenOptions};
use std::path::Path;
use serde::Serialize;
use std::process::Command;
use std::borrow::Cow;

#[derive(Serialize)]
struct TeilnehmerListe {
    names: Vec<String>,
}

// Datenstruktur für den Bot (leer, da wir keine zusätzlichen Daten brauchen)
struct Data;
type Error = Box<dyn std::error::Error + Send + Sync>; // WICHTIG: Send + Sync für Thread-Safety
type Context<'a> = poise::Context<'a, Data, Error>;

/// Command: Rolle auslesen und Namen in JSON speichern
#[poise::command(slash_command, prefix_command)]
async fn update_rolle(ctx: Context<'_>) -> Result<(), Error> {
    let role_id = get_role_id();
    let guild_id = ctx.guild_id().ok_or("Nicht in einem Server")?;

    // Hole alle Mitglieder des Servers ASYNCHRON (Send-safe!)
    let members = ctx.http().get_guild_members(guild_id, None, None).await?;

    // Filtere Mitglieder mit der gewünschten Rolle
    let names: Vec<String> = members
        .iter()
        .filter(|member| member.roles.contains(&role_id))
        .map(|member| member.user.name.clone())
        .collect();

    // Speichere in JSON
    let teilnehmer = TeilnehmerListe { names };
    let path = Path::new("data/teilnehmer.json");
    std::fs::create_dir_all(path.parent().unwrap()).ok();
    let file = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open(path)?;
    serde_json::to_writer(file, &teilnehmer)?;

    ctx.say("Teilnehmerliste aktualisiert!").await?;
    Ok(())
}

/// Command: Wheel-Link senden
#[poise::command(slash_command, prefix_command)]
async fn spin(ctx: Context<'_>) -> Result<(), Error> {
    let wheel_url = "http://localhost:5000";
    ctx.say(format!("🎡 Drehe das Wheel hier: {}", wheel_url)).await?;
    Ok(())
}

/// Command: Python-Skript ausführen
#[poise::command(slash_command, prefix_command)]
async fn local_spin(ctx: Context<'_>) -> Result<(), Error> {
    let output = Command::new("python3")
        .arg("wheel.py")
        .output()
        .map_err(|e| format!("Fehler: {}", e))?;

    let result = String::from_utf8_lossy(&output.stdout);
    if output.status.success() {
        ctx.say(format!("🎡 Lokales Wheel: {}", result)).await?;
    } else {
        ctx.say(format!("❌ Fehler: {}", String::from_utf8_lossy(&output.stderr))).await?;
    }
    Ok(())
}

#[tokio::main]
async fn main() {
    // Lade Token aus config.json
    let token = config_json_access("config.json");

    // Framework-Konfiguration
    let framework = poise::Framework::builder()
        .options(poise::FrameworkOptions {
            commands: vec![update_rolle(), spin(), local_spin()],
            prefix_options: poise::PrefixFrameworkOptions {
                prefix: Some("!".into()),
                ..Default::default()
            },
            ..Default::default()
        })
        .setup(|ctx, _ready, framework| {
            Box::pin(async move {
                poise::builtins::register_globally(ctx, &framework.options().commands).await?;
                Ok(Data)
            })
        })
        .build();

    // Client erstellen
    let intents = GatewayIntents::GUILDS | GatewayIntents::GUILD_MEMBERS;
    let mut client = serenity::ClientBuilder::new(token, intents)
        .framework(framework)
        .await
        .expect("Fehler beim Erstellen des Clients");

    // Client starten
    if let Err(why) = client.start().await {
        println!("Client-Fehler: {:?}", why);
    }
}

fn config_json_access(path: &str) -> Cow<'static, str> {
    let config_file = File::open(path).expect("config.json nicht gefunden");
    let config: serde_json::Value = serde_json::from_reader(config_file).expect("Ungültige config.json");
    Cow::Owned(config["token"].as_str().expect("Token nicht gefunden").to_string())
}

pub fn get_role_id() -> RoleId {
    config_json_access("rolle_id").to_string().parse().unwrap()
}