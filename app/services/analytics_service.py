"""
Advanced Analytics Service
Gelişmiş analitik ve raporlama servisi
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from bson import ObjectId
from app.core.database import get_database

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Gelişmiş analitik servisi"""
    
    def __init__(self):
        pass
    
    async def get_comprehensive_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Kapsamlı analitik raporu
        """
        try:
            db = await get_database()
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Paralel veri toplama
            analytics_tasks = [
                self._get_cv_analytics(db, start_date, end_date),
                self._get_job_analytics(db, start_date, end_date),
                self._get_matching_analytics(db, start_date, end_date),
                self._get_user_behavior_analytics(db, start_date, end_date),
                self._get_performance_analytics(db, start_date, end_date)
            ]
            
            results = await asyncio.gather(*analytics_tasks)
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "cv_analytics": results[0],
                "job_analytics": results[1],
                "matching_analytics": results[2],
                "user_behavior": results[3],
                "performance": results[4],
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Kapsamlı analitik hatası: {e}")
            return {"error": str(e)}
    
    async def _get_cv_analytics(self, db, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """CV analitikleri"""
        try:
            # Toplam CV sayısı
            total_cvs = await db.cvs.count_documents({})
            
            # Dönem içi yeni CV'ler
            new_cvs = await db.cvs.count_documents({
                "uploaded_at": {"$gte": start_date, "$lte": end_date}
            })
            
            # CV durumları
            cv_statuses = await db.cvs.aggregate([
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]).to_list(None)
            
            # En çok kullanılan beceriler
            top_skills = await db.cvs.aggregate([
                {"$match": {"parsed_data.skills": {"$exists": True}}},
                {"$unwind": "$parsed_data.skills"},
                {"$group": {"_id": "$parsed_data.skills", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]).to_list(None)
            
            # Deneyim seviyesi dağılımı
            experience_distribution = await db.cvs.aggregate([
                {"$match": {"parsed_data.experience": {"$exists": True}}},
                {"$project": {
                    "experience_level": {
                        "$switch": {
                            "branches": [
                                {"case": {"$lte": [{"$size": "$parsed_data.experience"}, 2]}, "then": "Junior"},
                                {"case": {"$lte": [{"$size": "$parsed_data.experience"}, 5]}, "then": "Mid-Level"},
                                {"case": {"$gt": [{"$size": "$parsed_data.experience"}, 5]}, "then": "Senior"}
                            ],
                            "default": "Unknown"
                        }
                    }
                }},
                {"$group": {"_id": "$experience_level", "count": {"$sum": 1}}}
            ]).to_list(None)
            
            # Eğitim seviyesi dağılımı
            education_distribution = await db.cvs.aggregate([
                {"$match": {"parsed_data.education": {"$exists": True}}},
                {"$unwind": "$parsed_data.education"},
                {"$group": {"_id": "$parsed_data.education.degree", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]).to_list(None)
            
            return {
                "total_cvs": total_cvs,
                "new_cvs": new_cvs,
                "growth_rate": (new_cvs / total_cvs * 100) if total_cvs > 0 else 0,
                "status_distribution": cv_statuses,
                "top_skills": top_skills,
                "experience_distribution": experience_distribution,
                "education_distribution": education_distribution
            }
            
        except Exception as e:
            logger.error(f"CV analitik hatası: {e}")
            return {"error": str(e)}
    
    async def _get_job_analytics(self, db, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """İş ilanı analitikleri"""
        try:
            # Toplam iş ilanı sayısı
            total_jobs = await db.jobs.count_documents({})
            
            # Dönem içi yeni iş ilanları
            new_jobs = await db.jobs.count_documents({
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
            
            # Şirket bazında iş ilanı dağılımı
            company_distribution = await db.jobs.aggregate([
                {"$group": {"_id": "$company", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]).to_list(None)
            
            # Konum bazında dağılım
            location_distribution = await db.jobs.aggregate([
                {"$group": {"_id": "$location", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 15}
            ]).to_list(None)
            
            # En çok aranan beceriler
            most_demanded_skills = await db.jobs.aggregate([
                {"$match": {"required_skills": {"$exists": True}}},
                {"$unwind": "$required_skills"},
                {"$group": {"_id": "$required_skills", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]).to_list(None)
            
            # İş türü dağılımı
            job_type_distribution = await db.jobs.aggregate([
                {"$group": {"_id": "$employment_type", "count": {"$sum": 1}}}
            ]).to_list(None)
            
            # Aktif/pasif iş ilanları
            job_status_distribution = await db.jobs.aggregate([
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]).to_list(None)
            
            return {
                "total_jobs": total_jobs,
                "new_jobs": new_jobs,
                "growth_rate": (new_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                "company_distribution": company_distribution,
                "location_distribution": location_distribution,
                "most_demanded_skills": most_demanded_skills,
                "job_type_distribution": job_type_distribution,
                "status_distribution": job_status_distribution
            }
            
        except Exception as e:
            logger.error(f"İş ilanı analitik hatası: {e}")
            return {"error": str(e)}
    
    async def _get_matching_analytics(self, db, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Eşleştirme analitikleri"""
        try:
            # Toplam eşleştirme sayısı (log tablosundan)
            total_matches = await db.match_logs.count_documents({
                "timestamp": {"$gte": start_date, "$lte": end_date}
            })
            
            # Başarılı eşleştirmeler (yüksek skor)
            successful_matches = await db.match_logs.count_documents({
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "match_score": {"$gte": 70}
            })
            
            # Ortalama eşleştirme skoru
            avg_match_score = await db.match_logs.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$group": {"_id": None, "avg_score": {"$avg": "$match_score"}}}
            ]).to_list(None)
            
            avg_score = avg_match_score[0]["avg_score"] if avg_match_score else 0
            
            # Skor dağılımı
            score_distribution = await db.match_logs.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$bucket": {
                    "groupBy": "$match_score",
                    "boundaries": [0, 30, 50, 70, 85, 100],
                    "default": "Other",
                    "output": {"count": {"$sum": 1}}
                }}
            ]).to_list(None)
            
            # En çok eşleşen beceriler
            top_matching_skills = await db.match_logs.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$unwind": "$matched_skills"},
                {"$group": {"_id": "$matched_skills", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 15}
            ]).to_list(None)
            
            # Günlük eşleştirme trendi
            daily_matches = await db.match_logs.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}}
            ]).to_list(None)
            
            return {
                "total_matches": total_matches,
                "successful_matches": successful_matches,
                "success_rate": (successful_matches / total_matches * 100) if total_matches > 0 else 0,
                "average_score": round(avg_score, 2),
                "score_distribution": score_distribution,
                "top_matching_skills": top_matching_skills,
                "daily_trend": daily_matches
            }
            
        except Exception as e:
            logger.error(f"Eşleştirme analitik hatası: {e}")
            return {"error": str(e)}
    
    async def _get_user_behavior_analytics(self, db, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Kullanıcı davranış analitikleri"""
        try:
            # API kullanım istatistikleri
            api_usage = await db.api_logs.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$group": {
                    "_id": "$endpoint",
                    "count": {"$sum": 1},
                    "avg_response_time": {"$avg": "$response_time"}
                }},
                {"$sort": {"count": -1}}
            ]).to_list(None)
            
            # En aktif kullanıcılar
            active_users = await db.user_activity.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$group": {
                    "_id": "$user_id",
                    "activity_count": {"$sum": 1},
                    "last_activity": {"$max": "$timestamp"}
                }},
                {"$sort": {"activity_count": -1}},
                {"$limit": 20}
            ]).to_list(None)
            
            # Sayfa görüntüleme istatistikleri
            page_views = await db.page_views.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$group": {"_id": "$page", "views": {"$sum": 1}}},
                {"$sort": {"views": -1}}
            ]).to_list(None)
            
            # Hata istatistikleri
            error_stats = await db.error_logs.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$group": {
                    "_id": "$error_type",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]).to_list(None)
            
            return {
                "api_usage": api_usage,
                "active_users": active_users,
                "page_views": page_views,
                "error_stats": error_stats
            }
            
        except Exception as e:
            logger.error(f"Kullanıcı davranış analitik hatası: {e}")
            return {"error": str(e)}
    
    async def _get_performance_analytics(self, db, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Performans analitikleri"""
        try:
            # Ortalama yanıt süreleri
            avg_response_times = await db.api_logs.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$group": {
                    "_id": "$endpoint",
                    "avg_response_time": {"$avg": "$response_time"},
                    "min_response_time": {"$min": "$response_time"},
                    "max_response_time": {"$max": "$response_time"}
                }},
                {"$sort": {"avg_response_time": -1}}
            ]).to_list(None)
            
            # Sistem kaynak kullanımı
            system_metrics = await db.system_metrics.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$group": {
                    "_id": None,
                    "avg_cpu": {"$avg": "$cpu_usage"},
                    "avg_memory": {"$avg": "$memory_usage"},
                    "avg_disk": {"$avg": "$disk_usage"}
                }}
            ]).to_list(None)
            
            # Embedding işlem süreleri
            embedding_performance = await db.embedding_logs.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$group": {
                    "_id": "$operation_type",
                    "avg_duration": {"$avg": "$duration_ms"},
                    "total_operations": {"$sum": 1}
                }}
            ]).to_list(None)
            
            # Veritabanı performansı
            db_performance = await db.command("dbStats")
            
            return {
                "api_response_times": avg_response_times,
                "system_metrics": system_metrics[0] if system_metrics else {},
                "embedding_performance": embedding_performance,
                "database_stats": {
                    "collections": db_performance.get("collections", 0),
                    "data_size": db_performance.get("dataSize", 0),
                    "index_size": db_performance.get("indexSize", 0),
                    "storage_size": db_performance.get("storageSize", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Performans analitik hatası: {e}")
            return {"error": str(e)}
    
    async def generate_weekly_report(self) -> Dict[str, Any]:
        """
        Haftalık rapor oluştur
        """
        try:
            # Son 7 gün verilerini al
            analytics = await self.get_comprehensive_analytics(days=7)
            
            # Önemli metrikler
            highlights = {
                "new_cvs": analytics["cv_analytics"]["new_cvs"],
                "new_jobs": analytics["job_analytics"]["new_jobs"],
                "total_matches": analytics["matching_analytics"]["total_matches"],
                "average_match_score": analytics["matching_analytics"]["average_score"],
                "top_skills": analytics["cv_analytics"]["top_skills"][:5],
                "top_companies": analytics["job_analytics"]["company_distribution"][:5]
            }
            
            # Trend analizi
            trends = await self._analyze_trends(analytics)
            
            # Öneriler
            recommendations = await self._generate_recommendations(analytics)
            
            return {
                "report_type": "weekly",
                "period": analytics["period"],
                "highlights": highlights,
                "trends": trends,
                "recommendations": recommendations,
                "full_analytics": analytics,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Haftalık rapor oluşturma hatası: {e}")
            return {"error": str(e)}
    
    async def _analyze_trends(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Trend analizi"""
        try:
            trends = {}
            
            # CV trend
            cv_growth = analytics["cv_analytics"]["growth_rate"]
            if cv_growth > 10:
                trends["cv_trend"] = "Yüksek büyüme"
            elif cv_growth > 5:
                trends["cv_trend"] = "Orta büyüme"
            else:
                trends["cv_trend"] = "Düşük büyüme"
            
            # İş ilanı trend
            job_growth = analytics["job_analytics"]["growth_rate"]
            if job_growth > 15:
                trends["job_trend"] = "Yüksek büyüme"
            elif job_growth > 8:
                trends["job_trend"] = "Orta büyüme"
            else:
                trends["job_trend"] = "Düşük büyüme"
            
            # Eşleştirme başarı oranı
            success_rate = analytics["matching_analytics"]["success_rate"]
            if success_rate > 75:
                trends["matching_trend"] = "Mükemmel"
            elif success_rate > 50:
                trends["matching_trend"] = "İyi"
            else:
                trends["matching_trend"] = "Geliştirilmeli"
            
            return trends
            
        except Exception as e:
            logger.error(f"Trend analizi hatası: {e}")
            return {}
    
    async def _generate_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Öneriler oluştur"""
        try:
            recommendations = []
            
            # CV analizi bazlı öneriler
            cv_growth = analytics["cv_analytics"]["growth_rate"]
            if cv_growth < 5:
                recommendations.append("CV yükleme sürecini kolaylaştırın")
            
            # İş ilanı bazlı öneriler
            job_growth = analytics["job_analytics"]["growth_rate"]
            if job_growth < 8:
                recommendations.append("Daha fazla şirketi platforma davet edin")
            
            # Eşleştirme bazlı öneriler
            avg_score = analytics["matching_analytics"]["average_score"]
            if avg_score < 60:
                recommendations.append("Eşleştirme algoritmalarını iyileştirin")
            
            # Genel öneriler
            recommendations.extend([
                "Kullanıcı geri bildirimlerini toplayın",
                "Sistem performansını izleyin",
                "Yeni özellikler ekleyin"
            ])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Öneri oluşturma hatası: {e}")
            return ["Sistem analizi yapılamadı"]

# Global analytics service instance
analytics_service = AnalyticsService()
